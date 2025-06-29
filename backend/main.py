from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from flows.orchestrator import AgentOrchestrator
from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager

load_dotenv()

app = FastAPI(
    title="AgentFlow API",
    description="Virtual AI Office Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
orchestrator = AgentOrchestrator()
memory_manager = MemoryManager()
approval_manager = ApprovalManager()

class ProjectRequest(BaseModel):
    vision: str
    user_name: Optional[str] = "User"
    approval_mode: Optional[str] = "manual"

class ApprovalResponse(BaseModel):
    action: str  # approve, deny, edit, retry
    feedback: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    agent: Optional[str] = None
    limit: Optional[int] = 5

class ConversationMessage(BaseModel):
    message: str
    project_id: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "AgentFlow API is running"}

@app.post("/api/conversation/start")
async def start_conversation(request: ConversationMessage):
    """Start conversation with Cofounder agent"""
    try:
        result = await orchestrator.start_conversation(request.message)
        return {"response": result["response"], "conversation_id": result["conversation_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/{conversation_id}/message")
async def send_message(conversation_id: str, request: ConversationMessage):
    """Continue conversation with agent"""
    try:
        result = await orchestrator.continue_conversation(conversation_id, request.message)
        return {"response": result["response"], "ready_for_approval": result.get("ready_for_approval", False)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start-project")
async def start_project(request: ProjectRequest):
    """Start a new project with the Cofounder agent"""
    try:
        result = await orchestrator.start_project(
            vision=request.vision,
            user_name=request.user_name,
            approval_mode=request.approval_mode
        )
        return {"status": "started", "project_id": result["project_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    return await orchestrator.get_agents_status()

@app.get("/api/memory/graph")
async def get_memory_graph():
    """Get the current memory graph state"""
    return await memory_manager.graph_memory.get_graph_state()

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    return await memory_manager.get_memory_stats()

@app.post("/api/memory/export")
async def export_memory():
    """Export all memory data"""
    try:
        exported_files = await memory_manager.export_all_outputs()
        return {"status": "exported", "files": exported_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/search")
async def search_memory(query: str, agent: Optional[str] = None, limit: int = 5):
    """Semantic search across memory"""
    try:
        results = await memory_manager.semantic_search(
            query=query,
            agent_name=agent,
            limit=limit
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/{conversation_id}/approve")
async def approve_conversation(conversation_id: str):
    """Approve conversation and start task distribution"""
    try:
        result = await orchestrator.approve_and_distribute(conversation_id)
        return {"status": "approved", "project_id": result["project_id"], "tasks": result["tasks"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/execute")
async def execute_agent(request: dict):
    """Execute specific agent with task"""
    try:
        agent_name = request["agent"]
        task = request["task"]
        result = await orchestrator.execute_single_agent(agent_name, task)
        return {"status": "started", "agent": agent_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/config")
async def update_agent_configs(configs: dict):
    """Update agent configurations"""
    try:
        result = await orchestrator.update_agent_configs(configs)
        return {"status": "updated", "configs": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/config")
async def get_agent_configs():
    """Get current agent configurations"""
    try:
        configs = await orchestrator.get_agent_configs()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/outputs")
async def get_outputs():
    """Get all generated outputs"""
    return await orchestrator.get_outputs()

@app.post("/api/approvals/{approval_id}/respond")
async def handle_approval_response(approval_id: str, response: ApprovalResponse):
    """Handle approval response"""
    try:
        result = await approval_manager.handle_response(
            approval_id, response.action, response.feedback
        )
        return {"status": "processed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
async def get_timeline():
    """Get execution timeline"""
    return await orchestrator.get_timeline()

@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Get pending approval requests"""
    return await approval_manager.get_pending_approvals()

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory statistics"""
    return await memory.get_graph_state()

@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Get all pending approvals"""
    approvals = await approval_manager.get_pending_approvals()
    return {"approvals": approvals}

@app.delete("/api/memory/clear")
async def clear_memory():
    """Clear all memory - USE WITH CAUTION"""
    try:
        await memory_manager.clear_all_memory()
        return {"status": "cleared", "message": "All memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    orchestrator.close()
    memory_manager.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)