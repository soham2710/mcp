# AI Agent with AWS Bedrock - Complete System

A comprehensive AI agent system with multiple modes (Summarizer, Router, Explainer, Quizzer) built using AWS Bedrock, FastAPI backend, NextJS frontend, and FastMCP server integration.

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   NextJS        │    │   FastAPI        │    │   AWS Bedrock   │
│   Frontend      │◄──►│   Backend        │◄──►│   Knowledge     │
│   (Port 3000)   │    │   (Port 8000)    │    │   Base          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude/VS     │    │   FastMCP        │    │   S3 + OpenSearch│
│   Code          │◄──►│   Server         │    │   Serverless    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 **Project Structure**

```
ai-agent-project/
├── README.md                    # This file
├── docker-compose.yml           # Container orchestration
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
│
├── frontend/                    # NextJS Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css     # Global styles
│   │   │   ├── layout.tsx      # Root layout
│   │   │   └── page.tsx        # Main page
│   │   └── components/
│   │       └── ChatInterface.tsx # Main chat component
│   ├── package.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   ├── tsconfig.json
│   └── .env.local
│
├── backend/                     # FastAPI Backend
│   ├── main.py                 # Main FastAPI application
│   ├── aws_setup.py            # AWS infrastructure setup
│   ├── requirements.txt        # Python dependencies
│   ├── test_mcp_integration.py # MCP integration tests
│   ├── .env                    # Environment variables
│   └── venv/                   # Python virtual environment
│
├── fastmcp-server/             # FastMCP Server
│   ├── fastmcp_server.py       # FastMCP server implementation
│   ├── requirements.txt        # FastMCP dependencies
│   └── venv-fastmcp/           # FastMCP virtual environment
│
├── scripts/                    # Utility scripts
│   ├── setup.sh               # Complete setup script
│   ├── start-all.sh           # Start all services
│   ├── stop-all.sh            # Stop all services
│   └── test-system.sh         # System integration tests
│
└── docs/                       # Documentation
    ├── api.md                  # API documentation
    ├── deployment.md           # Deployment guide
    └── troubleshooting.md      # Common issues
```

## 🚀 **Quick Start**

### **Prerequisites**

- **Node.js 18+** and npm
- **Python 3.11+**
- **AWS Account** with Bedrock access
- **Docker** (optional, for LocalStack)
- **VS Code** (for Claude integration)

### **1. Clone and Setup**

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-agent-project

# Copy environment template
cp .env.example .env

# Make scripts executable (Linux/macOS)
chmod +x scripts/*.sh
```

### **2. AWS Configuration**

```bash
# Configure AWS CLI
aws configure
# Enter your Access Key ID, Secret Access Key, and region (us-east-1)

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### **3. Automated Setup**

```bash
# Run the complete setup script
./scripts/setup.sh

# Or follow manual setup below
```

### **4. Manual Setup**

#### **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up AWS infrastructure (optional - creates Knowledge Base)
python aws_setup.py

# Start backend
uvicorn main:app --reload --port 8000
```

#### **Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### **FastMCP Server Setup**
```bash
cd fastmcp-server

# Create virtual environment
python -m venv venv-fastmcp
source venv-fastmcp/bin/activate  # Windows: venv-fastmcp\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastMCP server
python fastmcp_server.py
```

### **5. Start All Services**

```bash
# Using the provided script
./scripts/start-all.sh

# Or manually in separate terminals:
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: FastMCP Server
cd fastmcp-server && source venv-fastmcp/bin/activate && python fastmcp_server.py
```

## 🎯 **Features**

### **AI Agent Modes**

1. **🤖 Summarizer**
   - Brief, detailed, or bullet-point summaries
   - Configurable length and style
   - Real-time text processing

2. **🧭 Router**
   - Intelligent query analysis
   - Response strategy determination
   - Query routing recommendations

3. **🎓 Explainer**
   - Detailed concept explanations
   - Step-by-step breakdowns
   - Examples and analogies

4. **📚 Quizzer**
   - Educational quiz generation
   - Multiple question types
   - Configurable difficulty levels

### **Frontend Features**

- **Modern UI**: React/NextJS with Tailwind CSS
- **Real-time Chat**: Interactive conversation interface
- **Mode Switching**: Easy agent mode selection
- **Quick Actions**: Summary and quiz generation modals
- **Responsive Design**: Mobile-friendly interface
- **Offline Support**: Demo mode when backend unavailable

### **Backend Features**

- **FastAPI**: High-performance async API
- **AWS Bedrock Integration**: Titan Text G1 Premier model
- **Knowledge Base**: RAG with Titan Embeddings V2
- **Conversation Management**: Persistent chat history
- **Health Monitoring**: System status endpoints
- **CORS Support**: Frontend integration ready

### **FastMCP Server Features**

- **Claude Integration**: VS Code and Claude Desktop support
- **Tool Exposure**: All agent functions as MCP tools
- **Resource Management**: Knowledge base and conversation access
- **Error Handling**: Robust error management
- **Async Operations**: High-performance communication

## 🔧 **Configuration**

### **Environment Variables**

#### **Backend (.env)**
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.titan-text-premier-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
KNOWLEDGE_BASE_ID=your_kb_id_here

# API Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Development settings
DEBUG=true
LOG_LEVEL=INFO
```

#### **Frontend (.env.local)**
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Development settings
NEXT_PUBLIC_DEV_MODE=true
NEXT_PUBLIC_MOCK_API=true

# Feature flags
NEXT_PUBLIC_ENABLE_SUMMARY_MODAL=true
NEXT_PUBLIC_ENABLE_QUIZ_MODAL=true
NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE=true
```

### **AWS Services Required**

- **Amazon Bedrock**: Text generation and embeddings
- **Amazon S3**: Document storage
- **Amazon OpenSearch Serverless**: Vector database
- **AWS IAM**: Permissions and roles

## 📖 **API Documentation**

### **Core Endpoints**

#### **Chat with AI Agent**
```bash
POST /chat
Content-Type: application/json

{
  "message": "Explain quantum computing",
  "agent_mode": "explainer",
  "conversation_id": "optional-uuid",
  "context": "optional additional context"
}
```

#### **Generate Summary**
```bash
POST /summarize
Content-Type: application/json

{
  "text": "Long text to summarize...",
  "summary_type": "brief|detailed|bullet_points",
  "max_length": 200
}
```

#### **Create Quiz**
```bash
POST /quiz
Content-Type: application/json

{
  "topic": "Machine Learning",
  "difficulty": "medium",
  "num_questions": 5,
  "question_type": "multiple_choice"
}
```

#### **Query Knowledge Base**
```bash
POST /knowledge-base/query
Content-Type: application/json

{
  "query": "AWS Bedrock features",
  "max_results": 5,
  "confidence_threshold": 0.7
}
```

### **Health and Status**

```bash
GET /health                    # System health check
GET /localstack-status         # LocalStack status (if enabled)
GET /test-mcp-connection       # Test MCP server connection
GET /mcp-status               # Comprehensive MCP status
```

## 🧪 **Testing**

### **Backend Testing**

```bash
cd backend

# Run MCP integration tests
python test_mcp_integration.py

# Test individual endpoints
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "agent_mode": "explainer"}'
```

### **Frontend Testing**

```bash
cd frontend

# Run development server and test in browser
npm run dev
# Visit http://localhost:3000

# Build for production
npm run build
npm run start
```

### **FastMCP Testing**

```bash
cd fastmcp-server

# Start FastMCP server (should show startup info)
python fastmcp_server.py

# Test with MCP Inspector (if installed)
npx @anthropic-ai/mcp-client test
```

## 🐳 **Docker Deployment**

### **Using Docker Compose**

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down
```

### **Individual Service Containers**

```bash
# Backend only
docker build -t ai-agent-backend ./backend
docker run -p 8000:8000 ai-agent-backend

# Frontend only
docker build -t ai-agent-frontend ./frontend
docker run -p 3000:3000 ai-agent-frontend
```

## 🔗 **Claude Integration**

### **VS Code Setup**

1. **Install Claude Extension** in VS Code
2. **Configure MCP** in Claude settings:

```json
{
  "mcpServers": {
    "ai-agent": {
      "command": "python",
      "args": ["path/to/fastmcp-server/fastmcp_server.py"],
      "env": {
        "PYTHONPATH": "path/to/fastmcp-server"
      }
    }
  }
}
```

### **Available MCP Tools**

- `chat_with_agent` - Chat with any agent mode
- `summarize_text` - Generate text summaries
- `create_quiz` - Generate educational quizzes
- `query_knowledge_base` - Search knowledge base
- `get_conversation` - Retrieve conversation history
- `list_agent_modes` - List available agent modes
- `check_system_health` - System health check

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Backend Won't Start**
```bash
# Check Python virtual environment
source venv/bin/activate
pip install -r requirements.txt

# Check AWS credentials
aws sts get-caller-identity

# Check port availability
netstat -an | grep :8000
```

#### **Frontend Build Errors**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### **AWS Bedrock Access Denied**
```bash
# Enable model access in AWS Console
# Go to Bedrock → Model access → Request access
# Enable: Titan Text G1 Premier, Titan Embeddings V2

# Check IAM permissions
aws iam get-user
```

#### **FastMCP Connection Issues**
```bash
# Verify FastAPI backend is running
curl http://localhost:8000/health

# Check FastMCP dependencies
pip install fastmcp httpx pydantic

# Test MCP server startup
python fastmcp_server.py
```

### **Debugging**

#### **Enable Debug Logging**
```bash
# Backend
export DEBUG=true
export LOG_LEVEL=DEBUG

# Frontend
export NEXT_PUBLIC_DEV_MODE=true
```

#### **Check Service Status**
```bash
# All services health check
./scripts/test-system.sh

# Individual service checks
curl http://localhost:8000/health      # Backend
curl http://localhost:3000             # Frontend
curl http://localhost:8000/mcp-status  # MCP integration
```

## 📊 **Performance Optimization**

### **Backend Optimization**

- **Connection Pooling**: Boto3 client reuse
- **Async Operations**: FastAPI async endpoints
- **Caching**: Response caching for repeated queries
- **Request Limits**: Rate limiting and timeout handling

### **Frontend Optimization**

- **Code Splitting**: NextJS automatic code splitting
- **Static Generation**: Pre-built pages where possible
- **Image Optimization**: NextJS Image component
- **Bundle Analysis**: Webpack bundle analyzer

### **AWS Cost Optimization**

- **Bedrock**: Use appropriate model sizes
- **S3**: Lifecycle policies for old documents
- **OpenSearch**: Right-size cluster capacity
- **Monitoring**: CloudWatch cost alerts

## 🔐 **Security**

### **AWS Security**

- **IAM Roles**: Least privilege access
- **VPC**: Network isolation (production)
- **Encryption**: Data encryption at rest and in transit
- **API Keys**: Secure credential management

### **Application Security**

- **CORS**: Proper origin configuration
- **Input Validation**: Pydantic models
- **Rate Limiting**: API endpoint protection
- **Error Handling**: Secure error messages

## 🚀 **Deployment**

### **Production Deployment**

#### **AWS Deployment**
- **Backend**: AWS Lambda + API Gateway or ECS
- **Frontend**: AWS Amplify or CloudFront + S3
- **Database**: DynamoDB for conversation storage
- **Monitoring**: CloudWatch logs and metrics

#### **Vercel Deployment (Frontend)**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

#### **Railway/Render Deployment (Backend)**
```bash
# Configure environment variables in dashboard
# Connect GitHub repository
# Auto-deploy on push
```

### **Environment-Specific Configuration**

#### **Development**
```bash
USE_MOCK_AWS=false
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

#### **Staging**
```bash
USE_MOCK_AWS=false
DEBUG=false
CORS_ORIGINS=["https://staging.yourapp.com"]
```

#### **Production**
```bash
USE_MOCK_AWS=false
DEBUG=false
CORS_ORIGINS=["https://yourapp.com"]
RATE_LIMIT_ENABLED=true
```

## 📈 **Monitoring and Analytics**

### **Health Monitoring**

- **Backend**: `/health` endpoint with detailed status
- **Frontend**: Error boundaries and user analytics
- **AWS**: CloudWatch metrics and alarms
- **FastMCP**: Connection status monitoring

### **Usage Analytics**

- **Conversation Tracking**: User interaction patterns
- **Agent Mode Usage**: Popular agent types
- **Performance Metrics**: Response times and success rates
- **Cost Monitoring**: AWS service usage

## 🤝 **Contributing**

### **Development Workflow**

1. **Fork** the repository
2. **Create** a feature branch
3. **Develop** with tests
4. **Test** thoroughly (backend, frontend, MCP)
5. **Document** changes
6. **Submit** pull request

### **Code Standards**

- **Backend**: Black formatting, type hints, docstrings
- **Frontend**: ESLint, Prettier, TypeScript
- **Git**: Conventional commits
- **Testing**: Unit tests for critical paths

## 📚 **Resources**

### **Documentation Links**

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [NextJS Documentation](https://nextjs.org/docs)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Claude MCP Documentation](https://docs.anthropic.com/claude/docs/mcp)

### **Support**

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: `/docs` folder
- **Examples**: `/examples` folder

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 **Acknowledgments**

- **Anthropic** for Claude and MCP
- **AWS** for Bedrock and cloud services
- **FastAPI** team for the excellent framework
- **NextJS** team for the React framework
- **Community** contributors and testers

---

## 🚀 **Quick Commands Reference**

```bash
# Setup
./scripts/setup.sh

# Start all services
./scripts/start-all.sh

# Test system
./scripts/test-system.sh

# Stop all services
./scripts/stop-all.sh

# Individual service commands
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
cd fastmcp-server && python fastmcp_server.py
```

## 🎯 **Next Steps**

1. **Explore** the chat interface at `http://localhost:3000`
2. **Test** different agent modes and features
3. **Integrate** with Claude in VS Code
4. **Customize** prompts and responses
5. **Deploy** to your preferred cloud platform
6. **Extend** with additional agent types

Happy building! 🚀