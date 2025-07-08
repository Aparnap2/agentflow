"""
Enhanced AgentFlow API with advanced agent capabilities and comprehensive reporting
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from loguru import logger
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
print(f"Loading environment from: {env_path}")
load_dotenv(env_path)

from flows.orchestrator import AgentOrchestrator
from outputs.report_generator import ReportGenerator
from analytics.predictor import SimplePredictor
from collaboration.agent_collaborator import AgentCollaborator
from approvals.advanced_approval import AdvancedApprovalManager, ApprovalType
from services.agent_service import AgentService
from services.report_service import ReportService
from communication.event_bus import event_bus
from workflows.langgraph_orchestrator import LangGraphOrchestrator
from api.agent_logs import router as logs_router
from auth.supabase_auth import supabase_auth
from database.supabase_db import supabase_db

# Global instances
orchestrator = None
report_generator = None
predictor = None
collaborator = None
advanced_approval_manager = None
agent_service = None
report_service = None
langgraph_orchestrator = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global orchestrator, report_generator, predictor, collaborator, agent_service, report_service, langgraph_orchestrator
    
    # Startup
    orchestrator = AgentOrchestrator()
    report_generator = ReportGenerator()
    predictor = SimplePredictor()
    collaborator = AgentCollaborator(orchestrator.memory_manager, orchestrator.memory_manager.vector_memory)
    advanced_approval_manager = AdvancedApprovalManager()
    agent_service = AgentService(orchestrator, orchestrator.memory_manager)
    report_service = ReportService(orchestrator, orchestrator.memory_manager)
    langgraph_orchestrator = LangGraphOrchestrator(orchestrator.agents)
    
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

# Include logging router
app.include_router(logs_router)

# Request models
class AuthRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class ProjectRequest(BaseModel):
    vision: str
    user_name: Optional[str] = "User"
    approval_mode: Optional[str] = "manual"

class ApprovalResponse(BaseModel):
    action: str
    feedback: Optional[str] = None

class ConversationRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None
    agent: Optional[str] = None

class CollaborationRequest(BaseModel):
    requesting_agent: str
    target_agent: str
    request_type: str
    context: Optional[Dict[str, Any]] = {}

# Auth endpoints
@app.post("/api/auth/signup")
async def signup(request: AuthRequest):
    """User signup"""
    try:
        result = await supabase_auth.sign_up(
            email=request.email,
            password=request.password,
            metadata={"name": request.name} if request.name else None
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signin")
async def signin(request: AuthRequest):
    """User signin"""
    try:
        result = await supabase_auth.sign_in(
            email=request.email,
            password=request.password
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/user")
async def get_current_user(user: dict = Depends(supabase_auth.verify_token)):
    """Get current user"""
    return user

@app.get("/api/projects")
async def get_user_projects(user: dict = Depends(supabase_auth.verify_token)):
    """Get user's projects"""
    try:
        projects = await supabase_db.get_user_projects(user["id"])
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(request: dict, user: dict = Depends(supabase_auth.verify_token)):
    """Create new project"""
    try:
        project = await supabase_db.create_project(user["id"], request)
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        if agent_service:
            return await agent_service.get_all_agents_status()
        else:
            # Fallback to orchestrator agents
            agents_status = {}
            for name, agent in orchestrator.agents.items():
                agents_status[name] = {
                    "name": name,
                    "status": "active",
                    "expertise": getattr(agent.personality, 'expertise', []),
                    "description": getattr(agent.personality, 'description', f"{name} agent")
                }
            return agents_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/list")
async def get_agents_list():
    """Get list of all available agents"""
    try:
        agents_info = {}
        for name, agent in orchestrator.agents.items():
            agents_info[name] = {
                "name": name,
                "type": agent.__class__.__name__,
                "expertise": getattr(agent.personality, 'expertise', []),
                "description": getattr(agent.personality, 'description', f"{name} specialist agent"),
                "model": getattr(agent.personality, 'model', 'deepseek/deepseek-chat:free')
            }
        return {
            "agents": agents_info,
            "total_count": len(agents_info),
            "categories": {
                "strategic": ["Cofounder", "Manager"],
                "business": ["Product", "Finance", "Marketing", "Legal"],
                "operations": ["Sales", "Operations", "Workflow", "Assistant"],
                "specialized": ["Closer", "Amplifier", "Money"]
            }
        }
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
        
        # Analyze actual outputs to generate predictions
        predictions = {
            "project_success": _analyze_project_success(outputs),
            "revenue_trend": _analyze_revenue_trend(outputs),
            "market_timing": _analyze_market_timing(outputs),
            "generated_at": datetime.now().isoformat()
        }
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _analyze_project_success(outputs: dict) -> dict:
    """Analyze project success based on agent outputs"""
    if not outputs:
        return {
            "success_probability": 0.5,
            "confidence_level": "low",
            "key_factors": ["Waiting for agent outputs"],
            "recommendations": ["Start project to generate analysis"]
        }
    
    # Calculate success probability based on actual outputs
    confidences = []
    factors = []
    
    for filename, data in outputs.items():
        if isinstance(data, dict) and 'confidence' in data:
            confidences.append(data['confidence'])
        
        agent = data.get('agent', '').lower()
        if agent == 'finance':
            factors.append("Financial projections completed")
        elif agent == 'product':
            factors.append("Product strategy defined")
        elif agent == 'marketing':
            factors.append("Marketing plan developed")
        elif agent == 'legal':
            factors.append("Legal compliance reviewed")
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    success_probability = min(0.95, avg_confidence * 1.2)
    
    return {
        "success_probability": success_probability,
        "confidence_level": "high" if success_probability > 0.8 else "medium" if success_probability > 0.6 else "low",
        "key_factors": factors or ["Analysis in progress"],
        "recommendations": ["Continue execution"] if success_probability > 0.7 else ["Review and strengthen strategy"]
    }

def _analyze_revenue_trend(outputs: dict) -> dict:
    """Analyze revenue trend from finance outputs"""
    for filename, data in outputs.items():
        if 'finance' in filename.lower() and isinstance(data, dict):
            finance_data = data.get('data', {})
            projections = finance_data.get('financial_projections', {})
            
            if projections:
                # Extract revenue values
                revenues = []
                for year_data in projections.values():
                    if isinstance(year_data, dict) and 'revenue' in year_data:
                        revenues.append(year_data['revenue'])
                
                if len(revenues) >= 2:
                    growth_rate = (revenues[-1] - revenues[0]) / revenues[0] if revenues[0] > 0 else 0
                    return {
                        "trend": "growing" if growth_rate > 0.2 else "stable" if growth_rate > -0.1 else "declining",
                        "growth_rate": round(growth_rate * 100, 1),
                        "next_year_prediction": int(revenues[-1] * (1 + growth_rate * 0.8)),
                        "confidence": data.get('confidence', 0.7)
                    }
            
            return {
                "trend": "positive",
                "growth_rate": 25,
                "next_year_prediction": 500000,
                "confidence": data.get('confidence', 0.7)
            }
    
    return {
        "trend": "unknown",
        "growth_rate": 0,
        "next_year_prediction": 0,
        "confidence": 0.5
    }

def _analyze_market_timing(outputs: dict) -> dict:
    """Analyze market timing from various outputs"""
    timing_score = 0.7  # Base score
    actions = []
    
    # Check for market-related outputs
    has_market_analysis = False
    for filename, data in outputs.items():
        if isinstance(data, dict):
            agent = data.get('agent', '').lower()
            if agent in ['marketing', 'product']:
                has_market_analysis = True
                timing_score += 0.1
    
    if timing_score > 0.8:
        optimal_timing = "now"
        actions = ["Accelerate go-to-market", "Secure funding", "Scale team"]
    elif timing_score > 0.6:
        optimal_timing = "soon"
        actions = ["Complete MVP", "Validate market fit", "Prepare launch"]
    else:
        optimal_timing = "wait"
        actions = ["Strengthen product", "Research market", "Build capabilities"]
    
    return {
        "optimal_timing": optimal_timing,
        "timing_score": round(timing_score, 2),
        "recommended_actions": actions
    }

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
        # Get actual collaboration history from orchestrator timeline
        timeline = await orchestrator.get_timeline()
        
        collaborations = []
        for entry in timeline:
            if entry.get("status") == "completed":
                collaborations.append({
                    "id": f"collab_{entry.get('agent', 'unknown')}",
                    "requesting_agent": "Orchestrator",
                    "target_agent": entry.get("agent", "Unknown"),
                    "type": "task_execution",
                    "status": entry.get("status", "unknown"),
                    "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                    "confidence": entry.get("confidence", 0.0)
                })
        
        return {"collaborations": collaborations}
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

@app.post("/api/reports/generate-pdf")
async def generate_pdf_report(request: dict):
    """Generate PDF report from comprehensive data"""
    try:
        report_type = request.get("report_type", "comprehensive")
        
        # Get comprehensive report data
        outputs = await orchestrator.get_outputs()
        report_data = await report_generator.generate_comprehensive_report(outputs)
        
        # Generate PDF
        pdf_path = await report_generator.generate_pdf_report(report_data, report_type)
        
        return {
            "status": "success",
            "pdf_path": pdf_path,
            "download_url": f"/api/reports/download/{pdf_path.split('/')[-1]}",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    """Download generated report file"""
    try:
        from fastapi.responses import FileResponse
        import os
        
        # Check both PDF and HTML directories
        pdf_path = f"outputs/pdfs/{filename}"
        html_path = f"outputs/reports/{filename}"
        
        if os.path.exists(pdf_path):
            return FileResponse(
                path=pdf_path,
                filename=filename,
                media_type='application/pdf'
            )
        elif os.path.exists(html_path):
            return FileResponse(
                path=html_path,
                filename=filename,
                media_type='text/html'
            )
        else:
            raise HTTPException(status_code=404, detail="Report file not found")
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
        result = await orchestrator.approval_manager.handle_response(
            request_id=approval_id,
            action=response.action,
            feedback=response.feedback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/start")
async def start_conversation(request: ConversationRequest, user: dict = Depends(supabase_auth.verify_token)):
    """Start conversation with Cofounder agent"""
    try:
        result = await orchestrator.start_conversation(request.message)
        
        # Save conversation to database
        await supabase_db.save_conversation(user["id"], {
            "id": result["conversation_id"],
            "messages": [{"role": "user", "content": request.message}],
            "status": "active"
        })
        
        return {"response": result["response"], "conversation_id": result["conversation_id"], "ready_for_approval": result.get("ready_for_approval", False)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/{conversation_id}/message")
async def continue_conversation(conversation_id: str, request: ConversationRequest):
    """Continue conversation with agent"""
    try:
        result = await orchestrator.continue_conversation(conversation_id, request.message)
        return {"response": result["response"], "ready_for_approval": result["ready_for_approval"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/{conversation_id}/approve")
async def approve_conversation(conversation_id: str, user: dict = Depends(supabase_auth.verify_token)):
    """Approve conversation and start task distribution"""
    try:
        result = await orchestrator.approve_and_distribute(conversation_id)
        
        # Create project in database
        project_data = {
            "name": f"Project {result['project_id']}",
            "vision": "Auto-generated from conversation",
            "status": "in_progress",
            "conversation_id": conversation_id
        }
        await supabase_db.create_project(user["id"], project_data)
        
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

@app.websocket("/ws/agent-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(5)
            
            # Send agent status updates
            if orchestrator:
                agent_status = await orchestrator.get_agents_status()
                await websocket.send_json({
                    "type": "agent_status",
                    "data": agent_status,
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/approvals/advanced/pending")
async def get_advanced_pending_approvals():
    """Get pending approvals with advanced details"""
    try:
        if not advanced_approval_manager:
            return {"approvals": []}
        
        pending = await advanced_approval_manager.get_pending_approvals()
        return {
            "approvals": [
                {
                    "id": req.id,
                    "agent_name": req.agent_name,
                    "approval_type": req.approval_type.value,
                    "action_description": req.action_description,
                    "confidence_score": req.confidence_score,
                    "risk_level": req.risk_level,
                    "estimated_impact": req.estimated_impact,
                    "reasoning": req.reasoning,
                    "created_at": req.created_at.isoformat()
                }
                for req in pending
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/approvals/stats")
async def get_approval_stats():
    """Get approval system statistics"""
    try:
        if not advanced_approval_manager:
            return {"error": "Advanced approval manager not initialized"}
        
        stats = advanced_approval_manager.get_approval_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/personalities")
async def get_agent_personalities():
    """Get all agent personalities for UI display"""
    try:
        from agents.personalities import get_all_personalities
        personalities = get_all_personalities()
        
        return {
            agent_name: {
                "name": p.name,
                "traits": p.traits,
                "communication_style": p.communication_style,
                "expertise_areas": p.expertise_areas,
                "avatar_emoji": p.avatar_emoji,
                "background": p.background,
                "working_style": p.working_style
            }
            for agent_name, p in personalities.items()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/configs")
async def get_agent_configs():
    """Get agent configurations"""
    try:
        configs = await orchestrator.get_agent_configs()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/configs")
async def update_agent_configs(configs: dict):
    """Update agent configurations"""
    try:
        result = await orchestrator.update_agent_configs(configs)
        return {"status": "success", "configs": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/domains")
async def get_domain_reports():
    """Get modular domain-specific reports"""
    try:
        if report_service:
            return await report_service.get_all_reports()
        else:
            return {"error": "Report service not initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/domains/{domain}")
async def get_domain_report(domain: str):
    """Get specific domain report"""
    try:
        report = await report_service.get_report(domain)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report for domain '{domain}' not found")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/communication/stats")
async def get_communication_stats():
    """Get inter-agent communication analytics"""
    try:
        return event_bus.get_communication_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/execute")
async def execute_langgraph_workflow(request: dict):
    """Execute LangGraph workflow with streaming"""
    try:
        result = await langgraph_orchestrator.execute_workflow(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/resume/{thread_id}")
async def resume_workflow(thread_id: str):
    """Resume workflow from checkpoint"""
    try:
        result = await langgraph_orchestrator.resume_from_checkpoint(thread_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/execute")
async def execute_agent(request: dict):
    """Execute specific agent"""
    try:
        agent_name = request.get("agent")
        task = request.get("task")
        
        if not agent_name or not task:
            raise HTTPException(status_code=400, detail="Agent name and task required")
        
        result = await orchestrator.execute_single_agent(agent_name, task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-execute")
async def auto_execute_project(request: dict):
    """Auto-execute project with agent coordination"""
    try:
        vision = request.get("vision")
        if not vision:
            raise HTTPException(status_code=400, detail="Vision required")
        
        result = await orchestrator.auto_execute_from_vision(vision)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-execute/status")
async def get_auto_execution_status():
    """Get auto-execution status"""
    try:
        return await orchestrator.get_auto_execution_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/logs/live")
async def get_live_agent_logs():
    """Get live agent execution logs"""
    try:
        status = await orchestrator.get_auto_execution_status()
        return {
            "logs": status.get("recent_logs", []),
            "status": status.get("status", "idle"),
            "total_entries": status.get("log_entries", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-coordination")
async def test_coordination():
    """Test agent coordination system"""
    try:
        test_vision = "AI-powered productivity app for remote workers with task management and team collaboration features"
        
        logger.info(f"🧪 Testing coordination with vision: {test_vision}")
        
        # Start coordination
        result = await orchestrator.auto_execute_from_vision(test_vision)
        
        # Get immediate status
        status = await orchestrator.get_auto_execution_status()
        
        return {
            "test_started": True,
            "result": result,
            "current_status": status,
            "message": "Check /api/agents/logs/live for real-time updates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/logs")
async def stream_logs():
    """Stream agent execution logs in real-time"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate_logs():
        while True:
            try:
                status = await orchestrator.get_auto_execution_status()
                logs = status.get("recent_logs", [])
                
                for log in logs[-5:]:  # Last 5 logs
                    yield f"data: {json.dumps(log)}\n\n"
                
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                break
    
    return StreamingResponse(generate_logs(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)