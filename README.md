# 🚀 AgentFlow - AI Virtual Office Platform

**Transform your startup idea into a complete business plan with AI agents working as your virtual team.**

## ✨ **Final MVP Features**

### 🧠 **8 Specialized AI Agents with Auto-Coordination**
- **🎯 Cofounder Agent** - Vision analysis and strategy
- **📋 Manager Agent** - Auto task assignment and coordination  
- **🛠️ Product Agent** - MVP definition and user personas
- **💰 Finance Agent** - Financial projections and pricing
- **📈 Marketing Agent** - Marketing strategy and campaigns
- **⚖️ Legal Agent** - Compliance and legal requirements
- **💼 Sales Agent** - Sales strategy and forecasting
- **🔧 Operations Agent** - Operations planning

### 🤝 **Auto-Coordination System**
- Manager automatically assigns tasks based on context
- Agents communicate and share insights with each other
- Coordinated execution with dependency management
- Real-time execution logs and status tracking

### 🔐 **Authentication & Database**
- Supabase authentication with demo mode fallback
- User projects and conversation persistence
- Agent outputs saved to database
- Row-level security for multi-tenant support

### 🧠 **Advanced Memory Systems**
- **Neo4j Graph Memory** - Agent relationships and context
- **Qdrant Vector Memory** - Semantic search and RAG
- **Redis State Management** - Real-time conversation state

## 🚀 **Quick Start**

### **1. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys (only OPENROUTER_API_KEY required)
nano .env
```

### **2. Backend Setup**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### **3. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### **4. Access AgentFlow**
- 🌐 **Frontend**: http://localhost:5173
- 🔧 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

## 🎯 **How to Use**

### **Method 1: Auto-Execute (Recommended)**
1. Visit http://localhost:5173
2. Sign up/Sign in (or use demo mode)
3. Start conversation with AI Cofounder
4. Approve vision → Auto-execution starts
5. Watch agents coordinate in real-time
6. Get comprehensive business analysis

### **Method 2: API Integration**
```python
# Start conversation
response = requests.post('http://localhost:8000/api/conversation/start', 
    json={'message': 'I want to create a productivity app'})

# Approve and auto-execute
requests.post(f'http://localhost:8000/api/conversation/{conversation_id}/approve')

# Watch execution logs
logs = requests.get('http://localhost:8000/api/agents/logs/live').json()
```

## 📊 **Key API Endpoints**

### **Authentication**
- `POST /api/auth/signup` - User registration
- `POST /api/auth/signin` - User login
- `GET /api/auth/user` - Get current user

### **Auto-Coordination**
- `POST /api/auto-execute` - Auto-execute project
- `GET /api/auto-execute/status` - Get execution status
- `GET /api/agents/logs/live` - Live execution logs

### **Projects & Data**
- `GET /api/projects` - User's projects
- `GET /api/outputs` - Agent outputs
- `GET /api/analytics/predictions` - Predictive analytics

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│   FastAPI Backend │────│  Memory Systems │
│   • Auth UI      │    │   • Auto-Coord   │    │  • Neo4j Graph  │
│   • Live Logs    │    │   • Agent Comm    │    │  • Qdrant Vector│
│   • Real-time    │    │   • LLM Integration│    │  • Redis State  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │   8 AI Agents   │
                       │  • Auto-Coord   │
                       │  • Inter-Comm   │
                       │  • LangGraph    │
                       └─────────────────┘
```

## 🔧 **Configuration**

### **Required**
- `OPENROUTER_API_KEY` - Get free key at [OpenRouter.ai](https://openrouter.ai)

### **Optional (Demo Mode Available)**
- `SUPABASE_URL` & `SUPABASE_ANON_KEY` - Database
- `NEO4J_URI` & credentials - Graph memory
- `QDRANT_URL` & `QDRANT_API_KEY` - Vector memory
- `REDIS_URL` - State management

## 🚀 **Production Deployment**

### **Backend**
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### **Frontend**
```bash
npm run build
serve -s dist
```

### **Database Setup**
1. Create Supabase project
2. Run `database/schema.sql` in SQL editor
3. Add environment variables

## 📈 **Current Status**

✅ **100% Complete - Production Ready MVP**
- 8 specialized agents with auto-coordination
- Real-time agent communication and execution
- Authentication and database integration
- Advanced memory systems with RAG
- Professional UI with live execution logs
- Comprehensive business analysis outputs
- Demo mode for easy testing

## 🎯 **Success Metrics**

- **Technical Excellence**: Full-stack AI platform with auto-coordination
- **Business Value**: Complete startup analysis with agent collaboration
- **User Experience**: Real-time visibility into AI agent workflows
- **Scalability**: Multi-tenant architecture with Supabase
- **Innovation**: First AI platform with true agent auto-coordination

## 🤝 **Contributing**

AgentFlow demonstrates advanced AI engineering patterns:
- LangGraph-based agent orchestration
- Auto-coordination and inter-agent communication
- Multi-modal memory systems with RAG
- Production-ready authentication and database
- Real-time execution visibility

## 📄 **License**

MIT License - Built for portfolio demonstration and commercial use.

---

**Ready to see AI agents coordinate and build your business plan automatically? Start AgentFlow and watch the magic happen!** 🚀