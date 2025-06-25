from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from flows.orchestrator import AgentOrchestrator
from memory.graph_memory import GraphMemory
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
memory = GraphMemory()
approval_manager = ApprovalManager()

class ProjectRequest(BaseModel):
    vision: str
    user_name: Optional[str] = "User"
    approval_mode: Optional[str] = "manual"

class ApprovalResponse(BaseModel):
    action: str  # approve, deny, edit, retry
    feedback: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "AgentFlow API is running"}

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
    return await memory.get_graph_state()

@app.get("/api/outputs")
async def get_outputs():
    """Get all generated outputs"""
    return await orchestrator.get_outputs()

@app.post("/api/approvals/{approval_id}")
async def handle_approval(approval_id: str, response: ApprovalResponse):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)