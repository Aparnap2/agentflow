# 🚀 AgentFlow Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Setup Instructions](#setup-instructions)
5. [User Guide](#user-guide)

## Overview

AgentFlow is a production-ready AI platform where 8 specialized agents collaborate to analyze, plan, and execute your startup vision. From initial concept to comprehensive business reports, experience the power of AI-driven entrepreneurship.

## Architecture

```
Frontend (React + Vite + Tailwind) 
    ↓ HTTP/WebSocket + Real-time Updates
Backend (FastAPI + Python + Pandas)
    ↓ Agent Orchestration + Approval Middleware
LangGraph Agent Network (8 Specialized Agents)
    ↓ Memory Operations + Tool Execution
Neo4j/Graphiti (Structured) + Qdrant (Semantic)
    ↓ External APIs + Tool Integrations
OpenRouter LLM + Crawl4AI + Reporting Suite
```

## Features

### 1. Personality-Driven Agents

Each agent has a unique personality with:
- Name and background
- Communication style
- Decision-making approach
- Expertise areas
- Working style

### 2. Guided Workflow

Users progress through a natural workflow:
1. **Start** - Share your vision or chat with AI Cofounder
2. **Conversation** - Refine your vision with the Cofounder
3. **Tasks** - Manager distributes tasks to specialist agents
4. **Outputs** - Review outputs from each agent
5. **Reports** - Generate comprehensive reports

### 3. Advanced Approval System

- Granular approval controls per agent and action type
- Confidence-based automatic approvals
- Risk assessment for each action
- Detailed approval history

### 4. Real-Time Monitoring

- WebSocket for live agent status updates
- Detailed agent cards with personality traits
- Progress indicators for each agent
- Timeline of all agent actions

## Setup Instructions

### Quick Start

```bash
# Start backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Start frontend
cd frontend
pnpm install
pnpm dev
```

### One-Command Startup

```bash
./start_agentflow.sh
```

## User Guide

1. **Start a Project**
   - Enter your startup vision or chat with AI Cofounder
   - Discuss and refine your idea

2. **Review and Approve Vision**
   - Cofounder will present a refined vision
   - Approve to proceed to task distribution

3. **Monitor Agent Progress**
   - Watch specialist agents work on your project
   - Approve actions when requested

4. **Review Outputs**
   - Explore outputs from each agent
   - Generate comprehensive reports

5. **Export and Share**
   - Download reports in PDF format
   - Share with stakeholders
