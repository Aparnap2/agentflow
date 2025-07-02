# 🚀 AgentFlow - AI Virtual Office Platform

**Transform your startup idea into a complete business plan with AI agents working as your virtual team.**

AgentFlow is a production-ready AI platform where 8 specialized agents collaborate to analyze, plan, and execute your startup vision. From initial concept to comprehensive business reports, experience the power of AI-driven entrepreneurship.

## ✨ **What Makes AgentFlow Special**

### 🧠 **8 Specialized AI Agents**
- **🎯 Cofounder Agent** - Captures and refines your vision
- **📋 Manager Agent** - Creates roadmaps and assigns tasks  
- **🛠️ Product Agent** - Develops product strategy and features
- **💰 Finance Agent** - Financial modeling and projections
- **📈 Marketing Agent** - Marketing strategy and campaigns
- **⚖️ Legal Agent** - Compliance and legal requirements
- **💼 Sales Agent** - Sales strategy and forecasting
- **🔧 Operations Agent** - Operations planning and optimization

### 🤝 **Real-Time Agent Collaboration**
- Agents share context and collaborate on complex decisions
- Cross-functional insights (Marketing → Finance customer data)
- Intelligent task distribution and parallel execution

### 🧠 **Advanced Memory Systems**
- **Neo4j Graph Memory** - Relationship mapping and context
- **Qdrant Vector Memory** - Semantic search and retrieval
- **Redis State Management** - Real-time conversation persistence

### 📊 **Executive-Grade Dashboards**
- Real-time KPI monitoring and predictive analytics
- Professional PDF/HTML report generation
- Interactive data visualization with charts
- Export capabilities for presentations

### 🎨 **Modern Tech Stack**
- **Backend**: FastAPI + LangGraph + OpenRouter LLMs
- **Frontend**: React + Tailwind CSS + Recharts
- **Memory**: Neo4j + Qdrant + Redis
- **AI**: DeepSeek/OpenRouter with 25+ specialized prompts

## 🚀 **Quick Start (60 seconds)**

### **Option 1: One-Command Startup**
```bash
git clone <repository-url>
cd agentflow
./start_agentflow.sh
```

### **Option 2: Manual Setup**

#### **1. Prerequisites**
- Python 3.8+ 
- Node.js 16+
- pnpm (recommended) or npm

#### **2. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required API Keys:**
- `OPENROUTER_API_KEY` - Get free key at [OpenRouter.ai](https://openrouter.ai)
- `NEO4J_URI` - Free at [Neo4j Aura](https://neo4j.com/cloud/aura/)
- `QDRANT_URL` - Free at [Qdrant Cloud](https://cloud.qdrant.io)
- `REDIS_URL` - Free at [Upstash](https://upstash.com)

#### **3. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### **4. Frontend Setup**
```bash
cd frontend
pnpm install
pnpm dev
```

#### **5. Access the Platform**
- 🌐 **Frontend**: http://localhost:5173
- 🔧 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

## 🎯 **How to Use AgentFlow**

### **Method 1: Conversational Approach**
1. Visit http://localhost:5173
2. Click "Chat with AI Cofounder"
3. Describe your startup idea naturally
4. Refine your vision through conversation
5. Approve to distribute tasks to specialist agents
6. Watch real-time collaboration and results

### **Method 2: Direct Project Start**
1. Click "Start Project"
2. Enter your detailed vision
3. Automatic task distribution to all agents
4. Monitor progress on the dashboard
5. Export comprehensive business reports

### **Method 3: API Integration**
```python
import requests

# Start conversation
response = requests.post('http://localhost:8000/api/conversation/start', 
    json={'message': 'I want to create a food delivery app'})

conversation_id = response.json()['conversation_id']

# Approve and distribute
requests.post(f'http://localhost:8000/api/conversation/{conversation_id}/approve')

# Get results
outputs = requests.get('http://localhost:8000/api/outputs').json()
```

## 📊 **Features Showcase**

### **🤖 Intelligent Conversation Flow**
- Natural language vision capture
- Context-aware follow-up questions
- Vision completeness detection
- Seamless handoff to specialist agents

### **⚡ Parallel Agent Execution**
- 8 agents working simultaneously
- Real-time progress monitoring
- Cross-agent data sharing
- Intelligent error handling and retries

### **📈 Advanced Analytics**
- Project success prediction
- Revenue trend forecasting
- Market timing analysis
- Risk assessment and mitigation

### **📋 Professional Reports**
- Executive dashboard with KPIs
- Financial projections and modeling
- Marketing intelligence and campaigns
- Legal compliance and risk analysis
- Sales forecasting and strategy
- PDF/HTML export capabilities

### **🔄 Real-Time Collaboration**
- Agent-to-agent communication
- Shared context and memory
- Cross-functional insights
- Collaborative decision making

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│   FastAPI Backend │────│  Memory Systems │
│   • Dashboard    │    │   • 25+ Endpoints │    │  • Neo4j Graph  │
│   • 13+ Pages    │    │   • Agent Orchestr│    │  • Qdrant Vector│
│   • Real-time UI │    │   • LLM Integration│    │  • Redis State  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │   8 AI Agents   │
                       │  • Specialized  │
                       │  • Collaborative│
                       │  • LLM-Powered  │
                       └─────────────────┘
```

## 🔧 **API Endpoints**

### **Core Conversation**
- `POST /api/conversation/start` - Start new conversation
- `POST /api/conversation/{id}/message` - Continue conversation
- `POST /api/conversation/{id}/approve` - Approve and distribute

### **Agent Management**
- `GET /api/agents/status` - Get all agent statuses
- `POST /api/agents/execute` - Execute specific agent
- `GET /api/outputs` - Get all agent outputs

### **Reports & Analytics**
- `GET /api/reports/comprehensive` - Full business report
- `POST /api/reports/generate-pdf` - Generate PDF report
- `GET /api/analytics/predictions` - Predictive analytics

### **Memory & Collaboration**
- `GET /api/memory/stats` - Memory system statistics
- `POST /api/collaboration/request` - Agent collaboration
- `GET /api/collaboration/history` - Collaboration history

## 🎨 **Frontend Pages**

- **🏠 Dashboard** - Executive overview and KPIs
- **💬 Conversation** - Chat with AI Cofounder
- **🎯 Vision** - Project vision and goals
- **👥 Agents** - Agent status and management
- **📊 Analytics** - Predictive insights
- **📋 Reports** - Comprehensive business reports
- **🏢 Virtual Office** - Agent collaboration view
- **⚙️ Settings** - Configuration and preferences

## 🔐 **Security & Privacy**

- API key encryption and secure storage
- No sensitive data stored in logs
- Conversation data encrypted in Redis
- CORS protection and input validation
- Optional local deployment for privacy

## 🚀 **Production Deployment**

### **Docker Deployment**
```bash
docker-compose up -d
```

### **Manual Production Setup**
```bash
# Backend
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Frontend
pnpm build
serve -s dist
```

### **Environment Variables for Production**
```bash
DEBUG=false
APPROVAL_MODE=auto
LOG_LEVEL=WARNING
```

## 📈 **Current Status**

✅ **95% Complete - Production Ready**
- 8 specialized agents with LLM integration
- Real-time conversation and collaboration
- Advanced memory systems (Neo4j + Qdrant + Redis)
- Professional dashboards and reports
- PDF/HTML export capabilities
- 25+ API endpoints fully functional
- 13+ frontend pages with real-time updates

## 🎯 **Success Metrics**

- **Technical Excellence**: Full-stack AI platform with advanced orchestration
- **Business Value**: Complete startup analysis in minutes vs weeks
- **User Experience**: Conversational interface with professional outputs
- **Scalability**: Cloud-ready architecture with enterprise features
- **Innovation**: Real-time AI agent collaboration with shared memory

## 🤝 **Contributing**

AgentFlow is designed as a showcase of advanced AI engineering. The codebase demonstrates:
- Production-ready FastAPI architecture
- Advanced LangGraph agent orchestration
- Multi-modal memory systems
- Real-time collaboration patterns
- Professional UI/UX design

## 📄 **License**

MIT License - Built for portfolio demonstration and commercial use.

---

**Ready to transform your startup idea into reality? Start AgentFlow and watch AI agents build your business plan in real-time!** 🚀