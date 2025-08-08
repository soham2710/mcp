'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, FileText, Route, HelpCircle, BookOpen, AlertCircle } from 'lucide-react';

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: string;
  metadata?: any;
  error?: boolean;
}

type AgentMode = 'summarizer' | 'router' | 'explainer' | 'quizzer';

interface AgentConfig {
  icon: any;
  color: string;
  name: string;
}

interface SummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface QuizModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Mock API service for development
const mockApiService = {
  async chat(data: any) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const responses = {
      summarizer: `📝 **Summary Mode Response:**\n\nI've analyzed your request: "${data.message}"\n\nKey points:\n• This appears to be a request for the summarizer agent\n• The summarizer specializes in creating concise, clear summaries\n• It can provide brief, detailed, or bullet-point formats\n\n*Note: This is a mock response. Connect to the FastAPI backend for full functionality.*`,
      
      router: `🧭 **Router Mode Response:**\n\nAnalyzing your query: "${data.message}"\n\nRouting Decision:\n• Query type: Information request\n• Recommended approach: Direct explanation\n• Complexity level: Medium\n• Best suited agent: Explainer\n\nI recommend switching to the Explainer mode for detailed information on this topic.\n\n*Note: This is a mock response. Connect to the FastAPI backend for full functionality.*`,
      
      explainer: `🎓 **Explainer Mode Response:**\n\nLet me explain regarding: "${data.message}"\n\nDetailed Explanation:\nThis is a comprehensive explanation that would break down complex concepts into understandable parts. The explainer mode specializes in:\n\n1. **Clear Explanations**: Making complex topics accessible\n2. **Step-by-step Breakdowns**: Logical progression of ideas\n3. **Examples and Analogies**: Real-world connections\n4. **Interactive Learning**: Encouraging follow-up questions\n\nWould you like me to dive deeper into any specific aspect?\n\n*Note: This is a mock response. Connect to the FastAPI backend for full functionality.*`,
      
      quizzer: `📚 **Quizzer Mode Response:**\n\nBased on your input: "${data.message}"\n\nI can create educational content including:\n\n**Sample Quiz Question:**\nWhat are the main components of an AI agent system?\n\nA) Frontend, Backend, Database\nB) UI, API, Knowledge Base, Models\nC) HTML, CSS, JavaScript\nD) Only neural networks\n\n*Correct Answer: B*\n\nExplanation: AI agent systems typically include user interfaces, APIs for communication, knowledge bases for context, and AI models for processing.\n\n*Note: This is a mock response. Connect to the FastAPI backend for full functionality.*`
    };
    
    return {
      response: responses[data.agent_mode as keyof typeof responses] || responses.explainer,
      conversation_id: 'mock-conversation-' + Date.now(),
      agent_mode: data.agent_mode,
      metadata: {
        kb_results_count: Math.floor(Math.random() * 5),
        conversation_length: Math.floor(Math.random() * 10) + 1
      }
    };
  },
  
  async summarize(data: any) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const summaries = {
      brief: "This is a brief summary of the provided text, highlighting the main points in 2-3 sentences.",
      detailed: "This is a detailed summary that provides comprehensive coverage of the text, including key details, context, and supporting information while maintaining the original meaning and structure.",
      bullet_points: "• Main point one from the text\n• Secondary important information\n• Key supporting details\n• Conclusion or final thoughts"
    };
    
    return {
      summary: summaries[data.summary_type as keyof typeof summaries] || summaries.brief,
      summary_type: data.summary_type
    };
  },
  
  async createQuiz(data: any) {
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    const quiz = `**${data.topic} Quiz**
Difficulty: ${data.difficulty.toUpperCase()}
Questions: ${data.num_questions}

**Question 1:** What is the primary focus of ${data.topic}?
A) Basic concepts only
B) Advanced applications
C) Comprehensive understanding including theory and practice
D) Historical background only

**Question 2:** Which approach is most effective for learning ${data.topic}?
A) Memorization alone
B) Hands-on practice with theoretical foundation  
C) Reading only
D) Watching videos exclusively

**Answer Key:**
1. C - Comprehensive understanding is essential
2. B - Combining practice with theory yields best results

*Note: This is a mock quiz. Connect to the FastAPI backend for AI-generated content.*`;
    
    return {
      quiz_content: quiz,
      topic: data.topic,
      difficulty: data.difficulty,
      num_questions: data.num_questions,
      question_type: data.question_type
    };
  }
};

const AgentModes: Record<AgentMode, AgentConfig> = {
  summarizer: { icon: FileText, color: 'bg-blue-500', name: 'Summarizer' },
  router: { icon: Route, color: 'bg-green-500', name: 'Router' },
  explainer: { icon: HelpCircle, color: 'bg-purple-500', name: 'Explainer' },
  quizzer: { icon: BookOpen, color: 'bg-orange-500', name: 'Quizzer' }
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedMode, setSelectedMode] = useState<AgentMode>('explainer');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if backend is available
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        setIsOnline(response.ok);
      } catch {
        setIsOnline(false);
      }
    };
    checkBackend();
    
    // Check every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
      mode: selectedMode
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      let data;
      
      if (isOnline) {
        // Try real API first
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: inputMessage,
            conversation_id: conversationId,
            agent_mode: selectedMode
          })
        });

        if (!response.ok) {
          throw new Error('Failed to send message');
        }

        data = await response.json();
      } else {
        // Use mock API
        data = await mockApiService.chat({
          message: inputMessage,
          conversation_id: conversationId,
          agent_mode: selectedMode
        });
      }
      
      setConversationId(data.conversation_id);
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        mode: selectedMode,
        metadata: data.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Bot className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Agent Assistant</h1>
              <div className="flex items-center space-x-2">
                <p className="text-sm text-gray-500">
                  Current mode: {AgentModes[selectedMode].name}
                </p>
                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={`text-xs ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
                  {isOnline ? 'Online' : 'Demo Mode'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSummaryModal(true)}
              className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
            >
              Quick Summary
            </button>
            <button
              onClick={() => setShowQuizModal(true)}
              className="px-3 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 text-sm"
            >
              Create Quiz
            </button>
            <button
              onClick={clearConversation}
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
            >
              Clear Chat
            </button>
          </div>
        </div>
        
        {/* Agent Mode Selector */}
        <div className="flex space-x-2 mt-4">
          {Object.entries(AgentModes).map(([mode, config]) => {
            const Icon = config.icon;
            return (
              <button
                key={mode}
                onClick={() => setSelectedMode(mode as AgentMode)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedMode === mode
                    ? `${config.color} text-white`
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{config.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to AI Agent Assistant
            </h3>
            <p className="text-gray-500 mb-4">
              Choose an agent mode and start your conversation
            </p>
            {!isOnline && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 max-w-md mx-auto">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  <span className="text-sm text-yellow-800">
                    Running in demo mode. Connect FastAPI backend for full functionality.
                  </span>
                </div>
              </div>
            )}
            <div className="text-sm text-gray-400">
              <p>• Summarizer: Get concise summaries of content</p>
              <p>• Router: Get help with directing your queries</p>
              <p>• Explainer: Get detailed explanations of topics</p>
              <p>• Quizzer: Create quizzes and test knowledge</p>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.error
                  ? 'bg-red-100 text-red-800'
                  : 'bg-white text-gray-900 shadow-sm border'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.role === 'assistant' && (
                  <Bot className="h-5 w-5 mt-0.5 text-blue-600" />
                )}
                {message.role === 'user' && (
                  <User className="h-5 w-5 mt-0.5" />
                )}
                <div className="flex-1">
                  {message.mode && (
                    <div className="text-xs opacity-75 mb-1">
                      {AgentModes[message.mode as AgentMode]?.name}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  {message.metadata && (
                    <div className="text-xs opacity-75 mt-1">
                      KB results: {message.metadata.kb_results_count}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white shadow-sm border rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <div className="flex space-x-4">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Ask the ${AgentModes[selectedMode].name.toLowerCase()}...`}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Summary Modal */}
      <SummaryModal 
        isOpen={showSummaryModal} 
        onClose={() => setShowSummaryModal(false)} 
      />
      
      {/* Quiz Modal */}
      <QuizModal 
        isOpen={showQuizModal} 
        onClose={() => setShowQuizModal(false)} 
      />
    </div>
  );
}

// Summary Modal Component
function SummaryModal({ isOpen, onClose }: SummaryModalProps) {
  const [text, setText] = useState('');
  const [summaryType, setSummaryType] = useState('brief');
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const generateSummary = async () => {
    if (!text.trim()) return;
    
    setIsLoading(true);
    try {
      let data;
      
      // Check if backend is available
      try {
        const response = await fetch('http://localhost:8000/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text,
            summary_type: summaryType
          })
        });

        if (response.ok) {
          data = await response.json();
        } else {
          throw new Error('Backend unavailable');
        }
      } catch {
        // Use mock API
        data = await mockApiService.summarize({
          text,
          summary_type: summaryType
        });
      }
      
      setSummary(data.summary);
    } catch (error) {
      console.error('Error generating summary:', error);
      setSummary('Error generating summary. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">Generate Summary</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Text to summarize
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full h-32 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Paste your text here..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Summary Type
            </label>
            <select
              value={summaryType}
              onChange={(e) => setSummaryType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="brief">Brief</option>
              <option value="detailed">Detailed</option>
              <option value="bullet_points">Bullet Points</option>
            </select>
          </div>
          
          <button
            onClick={generateSummary}
            disabled={!text.trim() || isLoading}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Generating...' : 'Generate Summary'}
          </button>
          
          {summary && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Summary
              </label>
              <div className="bg-gray-50 border rounded-lg p-3 whitespace-pre-wrap">
                {summary}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// Quiz Modal Component
function QuizModal({ isOpen, onClose }: QuizModalProps) {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [numQuestions, setNumQuestions] = useState(5);
  const [questionType, setQuestionType] = useState('multiple_choice');
  const [quiz, setQuiz] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const generateQuiz = async () => {
    if (!topic.trim()) return;
    
    setIsLoading(true);
    try {
      let data;
      
      // Check if backend is available
      try {
        const response = await fetch('http://localhost:8000/quiz', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            topic,
            difficulty,
            num_questions: numQuestions,
            question_type: questionType
          })
        });

        if (response.ok) {
          data = await response.json();
        } else {
          throw new Error('Backend unavailable');
        }
      } catch {
        // Use mock API
        data = await mockApiService.createQuiz({
          topic,
          difficulty,
          num_questions: numQuestions,
          question_type: questionType
        });
      }
      
      setQuiz(data.quiz_content);
    } catch (error) {
      console.error('Error generating quiz:', error);
      setQuiz('Error generating quiz. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">Create Quiz</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter quiz topic..."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Questions
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={numQuestions}
                onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Question Type
            </label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="multiple_choice">Multiple Choice</option>
              <option value="true_false">True/False</option>
              <option value="short_answer">Short Answer</option>
            </select>
          </div>
          
          <button
            onClick={generateQuiz}
            disabled={!topic.trim() || isLoading}
            className="w-full py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            {isLoading ? 'Creating Quiz...' : 'Create Quiz'}
          </button>
          
          {quiz && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Generated Quiz
              </label>
              <div className="bg-gray-50 border rounded-lg p-3 whitespace-pre-wrap max-h-96 overflow-y-auto">
                {quiz}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}