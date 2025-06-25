# 🧠 AgentFlow - Virtual AI Office Platform

A full-stack async AI office where intelligent agents collaborate to simulate a startup team with shared memory, tool-driven reasoning, and human-in-the-loop approvals.

## 🎯 Overview

AgentFlow simulates a complete startup team with specialized AI agents:
- 🧠 **Cofounder**: Captures vision, goals, target users
- 🧭 **Manager**: Breaks vision into workstreams + assigns agents  
- 🎯 **Product**: Defines MVP, features, personas
- 💸 **Finance**: Simulates budget, ROI, revenue options
- 📣 **Marketing**: Plans content, SEO, outreach
- ⚖️ **Legal**: Drafts ToS/Privacy + checks compliance

## 🔧 Tech Stack

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Agents**: LangGraph + LangChain + CrewAI
- **Memory**: Neo4j + Graphiti (structured), Qdrant (semantic)
- **Tools**: Crawl4AI, OpenRouter
- **Storage**: Local JSON/YAML + Supabase (optional)

## 🚀 Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend  
cd frontend
npm install
npm run dev

# Services (Docker)
docker-compose up -d
```

## 📁 Project Structure

```
agentflow/
├── frontend/            # React + Vite UI
├── backend/             # FastAPI, LangGraph, LangChain
├── data/                # Agent outputs
├── graph.db/            # Neo4j data
├── vector.db/           # Qdrant data
└── docker-compose.yml
```

## 🎭 Agent Workflow

1. User submits vision → Cofounder captures it
2. Manager builds roadmap + assigns work
3. Specialist agents work in parallel
4. Approval flows for critical decisions
5. Final outputs exported to `/data`

Built for portfolio/freelance showcasing.