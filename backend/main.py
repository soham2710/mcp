from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import boto3
import json
import uuid
from datetime import datetime
import logging
from botocore.exceptions import ClientError
import subprocess
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# AWS Configuration
AWS_REGION = "us-east-1"  # Change to your preferred region
BEDROCK_MODEL_ID = "amazon.titan-text-premier-v1:0"
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
bedrock = boto3.client('bedrock', region_name=AWS_REGION)

# Pydantic models
class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent_mode: Literal["summarizer", "router", "explainer", "quizzer"] = "explainer"
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_mode: str
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeBaseQuery(BaseModel):
    query: str
    max_results: int = 5
    confidence_threshold: float = 0.7

class QuizRequest(BaseModel):
    topic: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    num_questions: int = 5
    question_type: Literal["multiple_choice", "true_false", "short_answer"] = "multiple_choice"

class SummaryRequest(BaseModel):
    text: str
    summary_type: Literal["brief", "detailed", "bullet_points"] = "brief"
    max_length: Optional[int] = None

# Agent prompts and configurations
AGENT_PROMPTS = {
    "summarizer": """You are an expert summarizer. Your task is to create clear, concise summaries that capture the key points and essential information. 
    Adapt your summary style based on the request:
    - Brief: 2-3 sentences highlighting main points
    - Detailed: Comprehensive summary with key details and context
    - Bullet points: Organized list of main points
    
    Always maintain accuracy and preserve important context.""",
    
    "router": """You are an intelligent router. Your role is to:
    1. Analyze user queries and determine the most appropriate response strategy
    2. Identify the type of information or assistance needed
    3. Route requests to the appropriate specialized function or provide direct responses
    4. Suggest alternative approaches when the initial request needs clarification
    
    Always explain your routing decision briefly.""",
    
    "explainer": """You are an expert explainer. Your mission is to make complex topics accessible and understandable:
    1. Break down complex concepts into digestible parts
    2. Use analogies and examples when helpful
    3. Provide step-by-step explanations when appropriate
    4. Adjust complexity based on the apparent knowledge level
    5. Encourage follow-up questions
    
    Always aim for clarity and engagement.""",
    
    "quizzer": """You are an educational quiz creator. Your role is to:
    1. Generate relevant, well-structured questions based on provided topics
    2. Create questions at appropriate difficulty levels
    3. Provide clear answer choices for multiple choice questions
    4. Include explanations for correct answers
    5. Ensure questions test understanding, not just memorization
    
    Focus on learning outcomes and educational value."""
}

class AIAgentService:
    def __init__(self):
        self.knowledge_base_id = None  # Will be set when KB is created
        self.conversations = {}  # In-memory storage for demo
    
    async def invoke_bedrock_model(self, prompt: str, max_tokens: int = 2000) -> str:
        """Invoke the Bedrock Titan model"""
        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['results'][0]['outputText']
            
        except ClientError as e:
            logger.error(f"Bedrock invocation error: {e}")
            raise HTTPException(status_code=500, detail=f"Model invocation failed: {str(e)}")
    
    async def query_knowledge_base(self, query: str, max_results: int = 5) -> List[Dict]:
        """Query the knowledge base if available"""
        if not self.knowledge_base_id:
            return []
        
        try:
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for item in response.get('retrievalResults', []):
                results.append({
                    'content': item.get('content', {}).get('text', ''),
                    'score': item.get('score', 0.0),
                    'location': item.get('location', {})
                })
            
            return results
            
        except ClientError as e:
            logger.error(f"Knowledge base query error: {e}")
            return []
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request based on agent mode"""
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if new
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message to conversation
        self.conversations[conversation_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now()
        })
        
        # Get relevant context from knowledge base
        kb_context = await self.query_knowledge_base(request.message)
        kb_context_text = "\n".join([item['content'] for item in kb_context[:3]])
        
        # Build prompt based on agent mode
        system_prompt = AGENT_PROMPTS[request.agent_mode]
        
        # Construct full prompt
        prompt_parts = [system_prompt]
        
        if kb_context_text:
            prompt_parts.append(f"Relevant knowledge base context:\n{kb_context_text}")
        
        if request.context:
            prompt_parts.append(f"Additional context:\n{request.context}")
        
        # Add conversation history (last 5 messages)
        recent_messages = self.conversations[conversation_id][-5:]
        if len(recent_messages) > 1:
            conversation_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_messages[:-1]  # Exclude current message
            ])
            prompt_parts.append(f"Conversation history:\n{conversation_history}")
        
        prompt_parts.append(f"User query: {request.message}")
        prompt_parts.append(f"Respond as a {request.agent_mode}:")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Generate response
        response_text = await self.invoke_bedrock_model(full_prompt)
        
        # Add assistant response to conversation
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now()
        })
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            agent_mode=request.agent_mode,
            metadata={
                "kb_results_count": len(kb_context),
                "conversation_length": len(self.conversations[conversation_id])
            }
        )
    
    async def create_summary(self, request: SummaryRequest) -> str:
        """Create summary using the summarizer agent"""
        prompt = f"{AGENT_PROMPTS['summarizer']}\n\n"
        prompt += f"Text to summarize:\n{request.text}\n\n"
        prompt += f"Summary type: {request.summary_type}\n"
        
        if request.max_length:
            prompt += f"Maximum length: approximately {request.max_length} words\n"
        
        prompt += "Please provide the summary:"
        
        return await self.invoke_bedrock_model(prompt)
    
    async def create_quiz(self, request: QuizRequest) -> Dict:
        """Create quiz using the quizzer agent"""
        prompt = f"{AGENT_PROMPTS['quizzer']}\n\n"
        prompt += f"Topic: {request.topic}\n"
        prompt += f"Difficulty: {request.difficulty}\n"
        prompt += f"Number of questions: {request.num_questions}\n"
        prompt += f"Question type: {request.question_type}\n\n"
        prompt += "Please create the quiz in a structured format with questions, options (if applicable), and correct answers with explanations."
        
        quiz_content = await self.invoke_bedrock_model(prompt, max_tokens=3000)
        
        return {
            "quiz_content": quiz_content,
            "topic": request.topic,
            "difficulty": request.difficulty,
            "num_questions": request.num_questions,
            "question_type": request.question_type
        }

# Initialize the AI agent service
ai_agent = AIAgentService()

# API Routes
@app.get("/")
async def root():
    return {"message": "AI Agent API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint supporting different agent modes"""
    return await ai_agent.process_chat(request)

@app.post("/summarize")
async def summarize(request: SummaryRequest):
    """Create summary of provided text"""
    summary = await ai_agent.create_summary(request)
    return {"summary": summary, "summary_type": request.summary_type}

@app.post("/quiz")
async def create_quiz(request: QuizRequest):
    """Generate quiz on specified topic"""
    quiz = await ai_agent.create_quiz(request)
    return quiz

@app.post("/knowledge-base/query")
async def query_knowledge_base(request: KnowledgeBaseQuery):
    """Query the knowledge base directly"""
    results = await ai_agent.query_knowledge_base(
        request.query, 
        request.max_results
    )
    
    # Filter by confidence threshold
    filtered_results = [
        result for result in results 
        if result['score'] >= request.confidence_threshold
    ]
    
    return {
        "query": request.query,
        "results": filtered_results,
        "total_results": len(results),
        "filtered_results": len(filtered_results)
    }

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history"""
    if conversation_id not in ai_agent.conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": ai_agent.conversations[conversation_id]
    }

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation history"""
    if conversation_id not in ai_agent.conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del ai_agent.conversations[conversation_id]
    return {"message": "Conversation deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Bedrock connectivity
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": "Test connection",
                "textGenerationConfig": {
                    "maxTokenCount": 10,
                    "temperature": 0.1
                }
            })
        )
        
        return {
            "status": "healthy",
            "bedrock_connection": "OK",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test-mcp-connection")
async def test_mcp_connection():
    """Test connection to FastMCP server"""
    try:
        # Path to your FastMCP server (adjust as needed)
        fastmcp_path = "../fastmcp-server/fastmcp_server.py"
        
        # Test MCP server by sending a tools/list request
        process = subprocess.Popen(
            ['python', fastmcp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="../fastmcp-server"  # Set working directory
        )
        
        # Send MCP request to list available tools
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        # Send request and get response
        stdout, stderr = process.communicate(
            input=json.dumps(request) + '\n',
            timeout=10
        )
        
        if process.returncode == 0 and stdout:
            try:
                response = json.loads(stdout.strip())
                tools = response.get('result', {}).get('tools', [])
                
                return {
                    "status": "success",
                    "mcp_server_status": "connected",
                    "available_tools": [tool.get('name') for tool in tools],
                    "total_tools": len(tools),
                    "details": {
                        "tools": tools[:3]  # Show first 3 tools as sample
                    }
                }
            except json.JSONDecodeError:
                return {
                    "status": "partial_success",
                    "mcp_server_status": "running_but_communication_issue",
                    "stdout": stdout,
                    "stderr": stderr
                }
        else:
            return {
                "status": "error",
                "mcp_server_status": "failed_to_start",
                "error": stderr,
                "return_code": process.returncode
            }
            
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "status": "error",
            "mcp_server_status": "timeout",
            "error": "FastMCP server did not respond within 10 seconds"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "mcp_server_status": "not_found",
            "error": "FastMCP server file not found. Check the path."
        }
    except Exception as e:
        return {
            "status": "error",
            "mcp_server_status": "unknown_error",
            "error": str(e)
        }

@app.post("/test-mcp-tool")
async def test_mcp_tool(tool_name: str, tool_args: Dict[str, Any] = None):
    """Test a specific MCP tool"""
    try:
        fastmcp_path = "../fastmcp-server/fastmcp_server.py"
        
        # Test MCP tool call
        process = subprocess.Popen(
            ['python', fastmcp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="../fastmcp-server"
        )
        
        # Send MCP tool call request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": tool_args or {}
            }
        }
        
        stdout, stderr = process.communicate(
            input=json.dumps(request) + '\n',
            timeout=15
        )
        
        if process.returncode == 0 and stdout:
            try:
                response = json.loads(stdout.strip())
                return {
                    "status": "success",
                    "tool_name": tool_name,
                    "result": response.get('result'),
                    "execution_time": "< 15s"
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "tool_name": tool_name,
                    "error": "Invalid JSON response",
                    "stdout": stdout,
                    "stderr": stderr
                }
        else:
            return {
                "status": "error",
                "tool_name": tool_name,
                "error": stderr,
                "return_code": process.returncode
            }
            
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "status": "error",
            "tool_name": tool_name,
            "error": "Tool execution timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "tool_name": tool_name,
            "error": str(e)
        }

@app.get("/mcp-status")
async def get_mcp_status():
    """Get comprehensive MCP integration status"""
    try:
        # Test basic backend health
        backend_status = {
            "fastapi_backend": "healthy",
            "bedrock_connection": "checking...",
            "timestamp": datetime.now().isoformat()
        }
        
        # Test MCP connection
        mcp_test = await test_mcp_connection()
        
        # Test a simple tool
        tool_test = None
        if mcp_test.get("status") == "success":
            tool_test = await test_mcp_tool("list_agent_modes")
        
        return {
            "overall_status": "healthy" if mcp_test.get("status") == "success" else "issues_detected",
            "backend": backend_status,
            "mcp_server": mcp_test,
            "sample_tool_test": tool_test,
            "integration_working": mcp_test.get("status") == "success" and tool_test is not None,
            "recommendations": get_mcp_recommendations(mcp_test, tool_test)
        }
        
    except Exception as e:
        return {
            "overall_status": "error",
            "error": str(e),
            "recommendations": ["Check server logs", "Restart FastMCP server", "Verify file paths"]
        }

def get_mcp_recommendations(mcp_test: Dict, tool_test: Dict = None) -> List[str]:
    """Get recommendations based on test results"""
    recommendations = []
    
    if mcp_test.get("status") != "success":
        if "not_found" in mcp_test.get("mcp_server_status", ""):
            recommendations.append("Check FastMCP server file path")
            recommendations.append("Ensure FastMCP server is in the correct directory")
        elif "timeout" in mcp_test.get("mcp_server_status", ""):
            recommendations.append("FastMCP server is starting slowly - check for errors")
            recommendations.append("Ensure all dependencies are installed")
        else:
            recommendations.append("Check FastMCP server logs for errors")
            recommendations.append("Verify Python environment and dependencies")
    
    if tool_test and tool_test.get("status") != "success":
        recommendations.append("MCP tools are not working properly")
        recommendations.append("Check FastAPI backend is running on port 8000")
    
    if not recommendations:
        recommendations.append("✅ All systems working perfectly!")
        recommendations.append("MCP integration is ready for use")
    
    return recommendations


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)