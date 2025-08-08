# fastmcp_server.py
"""
FastMCP Server for AI Agent Integration
This server provides an interface between Claude and your AI Agent system using FastMCP
"""

import httpx
import json
import logging
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-agent-fastmcp")

# Configuration
FASTAPI_BASE_URL = "http://localhost:8000"

# Initialize FastMCP
mcp = FastMCP("AI Agent Assistant")

# HTTP client for communicating with FastAPI backend
http_client = httpx.AsyncClient(timeout=30.0)

@mcp.tool()
async def chat_with_agent(
    message: str,
    agent_mode: str = "explainer",
    conversation_id: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """
    Send a message to the AI agent with specified mode.
    
    Args:
        message: Message to send to the AI agent
        agent_mode: AI agent mode (summarizer, router, explainer, quizzer)
        conversation_id: Optional conversation ID to continue existing conversation
        context: Optional additional context for the query
    
    Returns:
        AI agent response
    """
    try:
        response = await http_client.post(
            f"{FASTAPI_BASE_URL}/chat",
            json={
                "message": message,
                "agent_mode": agent_mode,
                "conversation_id": conversation_id,
                "context": context
            }
        )
        response.raise_for_status()
        data = response.json()
        
        result = f"**Agent Mode:** {data['agent_mode'].title()}\n\n"
        result += f"**Response:**\n{data['response']}\n\n"
        result += f"**Conversation ID:** {data['conversation_id']}\n"
        
        if data.get('metadata'):
            result += f"**Knowledge Base Results Used:** {data['metadata'].get('kb_results_count', 0)}\n"
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Error communicating with AI agent: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def summarize_text(
    text: str,
    summary_type: str = "brief",
    max_length: Optional[int] = None
) -> str:
    """
    Generate a summary of provided text using the summarizer agent.
    
    Args:
        text: Text to summarize
        summary_type: Type of summary (brief, detailed, bullet_points)
        max_length: Maximum length of summary in words
    
    Returns:
        Generated summary
    """
    try:
        payload = {
            "text": text,
            "summary_type": summary_type
        }
        if max_length:
            payload["max_length"] = max_length
            
        response = await http_client.post(
            f"{FASTAPI_BASE_URL}/summarize",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        result = f"**Summary Type:** {data['summary_type'].title()}\n\n"
        result += f"**Summary:**\n{data['summary']}"
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Error generating summary: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def create_quiz(
    topic: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    question_type: str = "multiple_choice"
) -> str:
    """
    Generate a quiz on a specific topic using the quizzer agent.
    
    Args:
        topic: Topic for the quiz
        difficulty: Difficulty level (easy, medium, hard)
        num_questions: Number of questions to generate (1-20)
        question_type: Type of questions (multiple_choice, true_false, short_answer)
    
    Returns:
        Generated quiz content
    """
    try:
        response = await http_client.post(
            f"{FASTAPI_BASE_URL}/quiz",
            json={
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "question_type": question_type
            }
        )
        response.raise_for_status()
        data = response.json()
        
        result = f"**Quiz Topic:** {data['topic']}\n"
        result += f"**Difficulty:** {data['difficulty'].title()}\n"
        result += f"**Question Type:** {data['question_type'].replace('_', ' ').title()}\n"
        result += f"**Number of Questions:** {data['num_questions']}\n\n"
        result += "**Quiz Content:**\n"
        result += data['quiz_content']
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Error creating quiz: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def query_knowledge_base(
    query: str,
    max_results: int = 5,
    confidence_threshold: float = 0.7
) -> str:
    """
    Query the AI agent's knowledge base for relevant information.
    
    Args:
        query: Search query for the knowledge base
        max_results: Maximum number of results to return (1-20)
        confidence_threshold: Minimum confidence threshold (0.0-1.0)
    
    Returns:
        Knowledge base search results
    """
    try:
        response = await http_client.post(
            f"{FASTAPI_BASE_URL}/knowledge-base/query",
            json={
                "query": query,
                "max_results": max_results,
                "confidence_threshold": confidence_threshold
            }
        )
        response.raise_for_status()
        data = response.json()
        
        result = f"**Knowledge Base Query:** '{data['query']}'\n"
        result += f"**Results Found:** {data['filtered_results']} (of {data['total_results']} total)\n\n"
        
        if data['results']:
            for i, item in enumerate(data['results'], 1):
                result += f"**Result {i}** (Score: {item['score']:.3f}):\n"
                result += f"{item['content'][:500]}{'...' if len(item['content']) > 500 else ''}\n\n"
        else:
            result += "No results found matching your query and confidence threshold."
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Error querying knowledge base: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def get_conversation(conversation_id: str) -> str:
    """
    Retrieve conversation history by ID.
    
    Args:
        conversation_id: ID of the conversation to retrieve
    
    Returns:
        Conversation history
    """
    try:
        response = await http_client.get(
            f"{FASTAPI_BASE_URL}/conversations/{conversation_id}"
        )
        response.raise_for_status()
        data = response.json()
        
        result = f"**Conversation ID:** {data['conversation_id']}\n"
        result += f"**Total Messages:** {len(data['messages'])}\n\n"
        
        for i, message in enumerate(data['messages'], 1):
            timestamp = message.get('timestamp', 'Unknown time')
            result += f"**Message {i}** [{timestamp}]\n"
            result += f"**{message['role'].title()}:** {message['content']}\n\n"
        
        return result
        
    except httpx.HTTPError as e:
        if e.response and e.response.status_code == 404:
            return f"❌ Conversation not found: {conversation_id}"
        return f"❌ Error retrieving conversation: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def list_agent_modes() -> str:
    """
    List available AI agent modes and their descriptions.
    
    Returns:
        Available agent modes and descriptions
    """
    modes = {
        "summarizer": "Creates concise summaries of text content. Supports brief, detailed, and bullet-point formats.",
        "router": "Analyzes queries and determines the best response strategy. Routes requests appropriately.",
        "explainer": "Provides detailed explanations of complex topics. Breaks down concepts into digestible parts.",
        "quizzer": "Generates educational quizzes and questions on specified topics. Supports multiple question types."
    }
    
    result = "**Available AI Agent Modes:**\n\n"
    for mode, description in modes.items():
        result += f"🤖 **{mode.title()}:**\n   {description}\n\n"
    
    result += "💡 **Usage:** Use the `chat_with_agent` tool with the `agent_mode` parameter to specify which mode to use."
    
    return result

@mcp.tool()
async def check_system_health() -> str:
    """
    Check the health status of the AI Agent system.
    
    Returns:
        System health information
    """
    try:
        response = await http_client.get(f"{FASTAPI_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        result = "**System Health Check:**\n\n"
        result += f"**Status:** {data.get('status', 'Unknown')}\n"
        result += f"**Bedrock Connection:** {data.get('bedrock_connection', 'Unknown')}\n"
        result += f"**Timestamp:** {data.get('timestamp', 'Unknown')}\n"
        
        if data.get('status') == 'healthy':
            result += "\n✅ All systems operational!"
        else:
            result += f"\n⚠️ System issues detected: {data.get('error', 'Unknown error')}"
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Cannot connect to AI Agent backend: {str(e)}\n\nMake sure the FastAPI server is running on {FASTAPI_BASE_URL}"
    except Exception as e:
        return f"❌ Unexpected error checking health: {str(e)}"

@mcp.resource("ai-agent://conversations")
async def get_conversations_resource() -> str:
    """Resource for accessing conversation management endpoints."""
    return json.dumps({
        "description": "Conversation management endpoints",
        "available_endpoints": [
            "GET /conversations/{id} - Retrieve specific conversation",
            "DELETE /conversations/{id} - Delete conversation"
        ],
        "tools": [
            "get_conversation - Retrieve conversation by ID"
        ]
    }, indent=2)

@mcp.resource("ai-agent://knowledge-base")
async def get_knowledge_base_resource() -> str:
    """Resource for accessing knowledge base information."""
    return json.dumps({
        "description": "AI Agent Knowledge Base",
        "content": "Contains information about AI, machine learning, and AWS Bedrock",
        "tools": [
            "query_knowledge_base - Search the knowledge base"
        ],
        "supported_queries": [
            "Technical questions about AI/ML",
            "AWS Bedrock information",
            "Machine learning concepts"
        ]
    }, indent=2)

@mcp.resource("ai-agent://health")
async def get_health_resource() -> str:
    """Resource for system health information."""
    try:
        response = await http_client.get(f"{FASTAPI_BASE_URL}/health")
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch health status: {str(e)}"}, indent=2)

# Cleanup function
async def cleanup():
    """Clean up resources when server stops."""
    await http_client.aclose()

if __name__ == "__main__":
    import asyncio
    import atexit
    
    # Register cleanup function
    atexit.register(lambda: asyncio.run(cleanup()))
    
    # Run the FastMCP server
    mcp.run()