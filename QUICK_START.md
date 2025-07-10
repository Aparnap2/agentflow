# 🚀 AgentFlow MVP - Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 16+
- All environment variables configured in `.env`

## 🏃‍♂️ Start the System (2 Steps)

### Step 1: Start Backend
```bash
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

### Step 2: Start Frontend  
```bash
cd frontend
npm run dev
```

## 🌐 Access Points

- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🎯 Quick Demo Actions

### Test Backend API
```bash
# Health check
curl http://localhost:8000/api/health

# List all agents
curl http://localhost:8000/api/agents/list

# Test agent coordination
curl -X POST http://localhost:8000/api/test-coordination
```

### Frontend Demo Flow
1. **Visit**: http://localhost:5173
2. **View Dashboard**: See all 13 agents
3. **Click "Auto-Execute Demo"**: Watch agents work
4. **Monitor Progress**: Real-time updates
5. **View Results**: Generated business outputs

## 🔧 Troubleshooting

### Backend Won't Start
- Check `.env` file exists with API keys
- Verify Python dependencies: `pip install -r requirements.txt`
- Check ports: `lsof -i :8000`

### Frontend Won't Start  
- Install dependencies: `npm install`
- Check Node version: `node --version`
- Clear cache: `npm run clean` then `npm install`

### Agents Not Responding
- Check LLM providers: http://localhost:8000/api/health
- Verify API keys in `.env`
- Check backend logs: `tail -f backend/server.log`

## 📊 Success Indicators

✅ Backend health returns `"status": "healthy"`  
✅ All 13 agents listed in `/api/agents/list`  
✅ Frontend loads dashboard without errors  
✅ Agent cards show status and descriptions  
✅ Auto-execute generates agent outputs  

## 🎉 You're Ready!

Your AgentFlow MVP is now running and ready for demonstration. The system provides:

- **13 Specialized AI Agents**
- **Real-time Monitoring Dashboard**  
- **Automatic Agent Coordination**
- **Comprehensive Business Planning**
- **Professional Portfolio-Quality Interface**

**Happy Demoing! 🚀**
