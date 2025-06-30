"""
Enhanced AgentFlow API with advanced agent capabilities and comprehensive reporting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager

from flows.orchestrator import AgentOrchestrator
from outputs.report_generator import ReportGenerator
from analytics.predictor import SimplePredictor
from collaboration.agent_collaborator import AgentCollaborator

# Global instances
orchestrator = None
report_generator = None
predictor = None
collaborator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global orchestrator, report_generator
    
    # Startup
    orchestrator = AgentOrchestrator()
    report_generator = ReportGenerator()
    predictor = SimplePredictor()
    collaborator = AgentCollaborator(orchestrator.memory_manager, orchestrator.memory_manager.vector_memory)
    
    yield
    
    # Shutdown
    if orchestrator:
        orchestrator.close()

app = FastAPI(
    title="AgentFlow API",
    description="Advanced AI agent orchestration platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ProjectRequest(BaseModel):
    vision: str
    user_name: Optional[str] = "User"
    approval_mode: Optional[str] = "manual"

class ApprovalResponse(BaseModel):
    action: str  # approve, deny, edit, retry
    feedback: Optional[str] = None

class CollaborationRequest(BaseModel):
    requesting_agent: str
    target_agent: str
    request_type: str
    context: Optional[Dict[str, Any]] = {}

# API Endpoints
@app.post("/api/start-project")
async def start_project(request: ProjectRequest):
    """Start new project with enhanced agent capabilities"""
    try:
        result = await orchestrator.start_project(
            vision=request.vision,
            user_name=request.user_name,
            approval_mode=request.approval_mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents including new specialized agents"""
    try:
        return await orchestrator.get_agents_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/outputs")
async def get_outputs():
    """Get all generated outputs with enhanced formatting"""
    try:
        return await orchestrator.get_outputs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/comprehensive")
async def get_comprehensive_report():
    """Generate comprehensive business report from all agent outputs"""
    try:
        # Get all agent outputs
        outputs = await orchestrator.get_outputs()
        
        # Generate comprehensive report
        report = await report_generator.generate_comprehensive_report(outputs)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/predictions")
async def get_predictions():
    """Get predictive analytics and recommendations"""
    try:
        outputs = await orchestrator.get_outputs()
        
        predictions = {
            "project_success": predictor.predict_project_success(outputs),
            "revenue_trend": predictor.predict_revenue_trend(outputs.get("finance.json", {}).get("data", {})),
            "market_timing": predictor.predict_market_timing(outputs.get("cofounder.json", {}).get("data", {})),
            "generated_at": datetime.now().isoformat()
        }
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collaboration/request")
async def request_collaboration(request: CollaborationRequest):
    """Request collaboration between agents"""
    try:
        result = await collaborator.request_collaboration(
            requesting_agent=request.requesting_agent,
            target_agent=request.target_agent,
            request_type=request.request_type,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collaboration/history")
async def get_collaboration_history(agent_name: Optional[str] = None):
    """Get collaboration history"""
    try:
        history = await collaborator.get_collaboration_history(agent_name)
        return {"collaborations": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_type}")
async def get_specific_report(report_type: str):
    """Get specific report type (executive, marketing, financial, etc.)"""
    try:
        outputs = await orchestrator.get_outputs()
        
        if report_type in report_generator.report_templates:
            generator_func = report_generator.report_templates[report_type]
            report = await generator_func(outputs)
            return {
                "report_type": report_type,
                "data": report,
                "generated_at": report_generator._create_timestamp()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Report type '{report_type}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/graph")
async def get_memory_graph():
    """Get graph memory visualization data"""
    try:
        # Get graph context for visualization
        graph_data = {
            "nodes": [],
            "edges": [],
            "statistics": {
                "total_agents": len(orchestrator.agents),
                "total_tasks": 0,
                "total_outputs": 0
            }
        }
        
        # Add agent nodes
        for agent_name in orchestrator.agents.keys():
            graph_data["nodes"].append({
                "id": agent_name,
                "type": "agent",
                "label": agent_name,
                "status": "active"
            })
        
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get comprehensive memory statistics"""
    try:
        # Get memory stats from both systems
        vector_stats = await orchestrator.memory_manager.get_memory_stats()
        
        # Add graph memory stats if available
        graph_stats = {}
        try:
            if hasattr(orchestrator, 'graph_memory') and orchestrator.graph_memory.driver:
                with orchestrator.graph_memory.driver.session() as session:
                    result = session.run("MATCH (n) RETURN count(n) as nodes")
                    node_count = result.single()["nodes"]
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as relationships")
                    rel_count = result.single()["relationships"]
                    graph_stats = {"nodes": node_count, "relationships": rel_count, "status": "connected"}
            else:
                graph_stats = {"status": "fallback_mode"}
        except Exception:
            graph_stats = {"status": "unavailable"}
        
        return {
            "vector_memory": vector_stats.get("vector_memory", {}),
            "graph_memory": graph_stats,
            "exports": vector_stats.get("exports", {}),
            "last_updated": vector_stats.get("last_updated", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/export")
async def export_memory():
    """Export all memory data"""
    try:
        exported_files = await orchestrator.memory_manager.export_all_outputs()
        return {
            "status": "success",
            "exported_files": exported_files,
            "export_location": "data/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory/clear")
async def clear_memory():
    """Clear all memory data"""
    try:
        # Clear vector memory
        await orchestrator.memory_manager.vector_memory.clear_collection()
        
        # Clear graph memory if available
        try:
            if hasattr(orchestrator, 'graph_memory') and orchestrator.graph_memory.driver:
                with orchestrator.graph_memory.driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
        except Exception as e:
            logger.warning(f"Graph memory clear failed: {e}")
        
        return {"status": "success", "message": "All memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
async def get_timeline():
    """Get execution timeline with enhanced tracking"""
    try:
        return await orchestrator.get_timeline()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Get pending approvals"""
    try:
        approvals = await orchestrator.approval_manager.get_pending_approvals()
        return {"approvals": approvals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approvals/{approval_id}/respond")
async def respond_to_approval(approval_id: str, response: ApprovalResponse):
    """Respond to approval request"""
    try:
        result = await orchestrator.approval_manager.process_approval(
            approval_id=approval_id,
            action=response.action,
            feedback=response.feedback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_available": len(orchestrator.agents) if orchestrator else 0,
        "memory_systems": {
            "vector_memory": "available",
            "graph_memory": "available" if hasattr(orchestrator, 'graph_memory') else "fallback"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)