#!/bin/bash

# Final cleanup script for AgentFlow

echo "🧹 Performing final cleanup of AgentFlow..."

# Create backup directory
mkdir -p .backup/frontend
mkdir -p .backup/docs

# Move unnecessary files to backup
echo "📁 Moving unnecessary files to backup..."

# Backup unused enhanced components
mv frontend/src/EnhancedApp.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/SimpleEnhancedApp.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/WorkflowLayout.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/WorkflowSidebar.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/AgentTransition.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/EnhancedConversationPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/ExecutionPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/ResultsPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/contexts/WorkflowContext.jsx .backup/frontend/ 2>/dev/null || true

# Backup unnecessary MD files
mv ENHANCED_PRD.md .backup/docs/ 2>/dev/null || true
mv FIXES_TRACKER.md .backup/docs/ 2>/dev/null || true
mv FRONTEND_ALIGNMENT.md .backup/docs/ 2>/dev/null || true
mv FRONTEND_REFACTOR_PLAN.md .backup/docs/ 2>/dev/null || true
mv IMPLEMENTATION_EXECUTION_PLAN.md .backup/docs/ 2>/dev/null || true
mv IMPLEMENTATION_STATUS.md .backup/docs/ 2>/dev/null || true
mv IMPLEMENTATION_TRACKER.md .backup/docs/ 2>/dev/null || true
mv STRATEGIC_ROADMAP.md .backup/docs/ 2>/dev/null || true
mv ENHANCEMENT_PLAN.md .backup/docs/ 2>/dev/null || true
mv UI_UX_ENHANCEMENT.md .backup/docs/ 2>/dev/null || true
mv API_IMPORT_FIX.md .backup/docs/ 2>/dev/null || true
mv UI_INTEGRATION_SUMMARY.md .backup/docs/ 2>/dev/null || true
mv ENHANCED_UI_SUMMARY.md .backup/docs/ 2>/dev/null || true

# Create consolidated documentation
echo "📝 Creating consolidated documentation..."
cat > DOCUMENTATION.md << EOL
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

\`\`\`
Frontend (React + Vite + Tailwind) 
    ↓ HTTP/WebSocket + Real-time Updates
Backend (FastAPI + Python + Pandas)
    ↓ Agent Orchestration + Approval Middleware
LangGraph Agent Network (8 Specialized Agents)
    ↓ Memory Operations + Tool Execution
Neo4j/Graphiti (Structured) + Qdrant (Semantic)
    ↓ External APIs + Tool Integrations
OpenRouter LLM + Crawl4AI + Reporting Suite
\`\`\`

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

\`\`\`bash
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
\`\`\`

### One-Command Startup

\`\`\`bash
./start_agentflow.sh
\`\`\`

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
EOL

echo "✅ Cleanup complete!"