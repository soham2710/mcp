import ChatInterface from '../components/ChatInterface'

export default function Home() {
  return (
    <main className="h-screen bg-gray-50">
      <ChatInterface />
    </main>
  )
}

export const metadata = {
  title: 'AI Agent Assistant',
  description: 'Intelligent AI agent with multiple modes: summarizer, router, explainer, and quizzer',
}