"""
Agent Status API - Provides endpoints for retrieving agent status and performance metrics
Enhanced version with real-time updates and detailed metrics for the Hub Integration Model
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import asyncio
import json
from loguru import logger

from flows.orchestrator import AgentOrchestrator
from communication.event_bus import event_bus
from memory.memory_manager import OptimizedMemoryManager
from task_queue.enhanced_queue_manager import queue_manager
from task_queue.task_router import TaskRouter
from task_queue.cross_agent_validator import CrossAgentValidator

router = APIRouter(prefix="/api/agent-status", tags=["agent-status"])

class AgentStatusResponse(BaseModel):
    agent_name: str
    status: str  # active, idle, busy, error
    current_task: Optional[str] = None
    last_activity: str
    performance_metrics: Dict[str, Any]
    queue_status: Dict[str, Any]
    specializations: List[str] = Field(default_factory=list, description="Agent's specialized domains")
    collaboration_score: float = Field(default=0.0, description="Score indicating how well the agent collaborates")

class AgentPerformanceMetrics(BaseModel):
    tasks_completed: int
    success_rate: float
    avg_completion_time: float
    current_workload: int
    reliability_score: float
    
class DetailedAgentMetrics(BaseModel):
    tasks_completed: int
    success_rate: float
    avg_completion_time: float
    current_workload: int
    reliability_score: float
    task_distribution: Dict[str, int] = Field(description="Distribution of tasks by type")
    collaboration_metrics: Dict[str, float] = Field(description="Metrics for collaboration with other agents")
    error_rate: float = Field(description="Rate of errors in task execution")
    avg_response_time: float = Field(description="Average time to respond to requests")
    knowledge_sharing_score: float = Field(description="Score for knowledge sharing with other agents")

class AgentRelationship(BaseModel):
    source_agent: str
    target_agent: str
    strength: float = Field(description="Strength of relationship (0-1)")
    task_count: int = Field(description="Number of tasks shared")
    success_rate: float = Field(description="Success rate of collaborative tasks")
    last_interaction: str = Field(description="Timestamp of last interaction")

class AgentNetwork(BaseModel):
    nodes: List[str] = Field(description="List of agent names")
    relationships: List[AgentRelationship] = Field(description="Relationships between agents")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@router.get("/all", response_model=Dict[str, AgentStatusResponse])
async def get_all_agents_status() -> Dict[str, AgentStatusResponse]:
    """Get status of all agents"""
    try:
        orchestrator = AgentOrchestrator()
        
        # Initialize enhanced queue manager if not already done
        if not queue_manager.is_initialized:
            await queue_manager.initialize()
        
        agent_statuses = {}
        
        for agent_name, agent in orchestrator.agents.items():
            try:
                # Get agent's current status
                agent_status = await _get_agent_status(agent_name, agent)
                agent_statuses[agent_name] = agent_status
                
            except Exception as e:
                logger.error(f"Error getting status for agent {agent_name}: {e}")
                # Return error status for this agent
                agent_statuses[agent_name] = AgentStatusResponse(
                    agent_name=agent_name,
                    status="error",
                    current_task=None,
                    last_activity=datetime.now().isoformat(),
                    performance_metrics={
                        "tasks_completed": 0,
                        "success_rate": 0.0,
                        "avg_completion_time": 0.0,
                        "current_workload": 0,
                        "reliability_score": 0.0
                    },
                    queue_status={"error": str(e)}
                )
        
        return agent_statuses
        
    except Exception as e:
        logger.error(f"Error getting all agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_name}", response_model=AgentStatusResponse)
async def get_agent_status(agent_name: str) -> AgentStatusResponse:
    """Get status of a specific agent"""
    try:
        orchestrator = AgentOrchestrator()
        
        if agent_name not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        agent = orchestrator.agents[agent_name]
        return await _get_agent_status(agent_name, agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_name}/metrics", response_model=AgentPerformanceMetrics)
async def get_agent_performance_metrics(agent_name: str) -> AgentPerformanceMetrics:
    """Get detailed performance metrics for a specific agent"""
    try:
        orchestrator = AgentOrchestrator()
        
        if agent_name not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get performance metrics from task router and validator
        task_router = TaskRouter()
        validator = CrossAgentValidator()
        
        # Get metrics from task router
        router_metrics = task_router.agent_performance.get(agent_name, {})
        
        # Get reliability metrics from validator
        validator_metrics = validator.agent_reliability.get(agent_name, {})
        
        return AgentPerformanceMetrics(
            tasks_completed=router_metrics.get("tasks_completed", 0),
            success_rate=router_metrics.get("success_rate", 0.0),
            avg_completion_time=router_metrics.get("avg_completion_time", 0.0),
            current_workload=router_metrics.get("current_workload", 0),
            reliability_score=validator_metrics.get("reliability_score", 0.5)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_name}/detailed-metrics", response_model=DetailedAgentMetrics)
async def get_detailed_agent_metrics(agent_name: str) -> DetailedAgentMetrics:
    """Get comprehensive performance metrics for a specific agent"""
    try:
        orchestrator = AgentOrchestrator()
        
        if agent_name not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get performance metrics from task router and validator
        task_router = TaskRouter()
        validator = CrossAgentValidator()
        
        # Get metrics from task router
        router_metrics = task_router.agent_performance.get(agent_name, {})
        
        # Get reliability metrics from validator
        validator_metrics = validator.agent_reliability.get(agent_name, {})
        
        # Get task history to calculate task distribution
        task_history = task_router.task_history
        
        # Calculate task distribution
        task_distribution = {}
        for task in task_history:
            if agent_name in task.get("agents", []):
                task_type = task.get("task_type", "unknown")
                if task_type not in task_distribution:
                    task_distribution[task_type] = 0
                task_distribution[task_type] += 1
        
        # Calculate collaboration metrics
        collaboration_metrics = {}
        for other_agent in orchestrator.agents:
            if other_agent != agent_name:
                # Calculate collaboration score based on shared tasks
                shared_tasks = sum(1 for task in task_history 
                                  if agent_name in task.get("agents", []) and 
                                  other_agent in task.get("agents", []))
                
                if shared_tasks > 0:
                    # Calculate success rate of collaborative tasks
                    successful_tasks = sum(1 for task in task_history 
                                         if agent_name in task.get("agents", []) and 
                                         other_agent in task.get("agents", []) and
                                         task.get("outcome") == "success")
                    
                    success_rate = successful_tasks / shared_tasks if shared_tasks > 0 else 0
                    collaboration_metrics[other_agent] = success_rate
        
        # Calculate error rate from validation history
        validation_history = validator.validation_history
        agent_validations = sum(1 for v in validation_history if agent_name in v.get("agents_involved", []))
        agent_errors = sum(1 for v in validation_history 
                         if agent_name in v.get("agents_involved", []) and not v.get("is_valid", True))
        
        error_rate = agent_errors / agent_validations if agent_validations > 0 else 0
        
        # Estimate average response time (placeholder - would need actual timing data)
        avg_response_time = router_metrics.get("avg_completion_time", 150)
        
        # Calculate knowledge sharing score based on contributions to shared context
        # This is a placeholder - would need actual knowledge sharing metrics
        knowledge_sharing_score = 0.5
        
        return DetailedAgentMetrics(
            tasks_completed=router_metrics.get("tasks_completed", 0),
            success_rate=router_metrics.get("success_rate", 0.0),
            avg_completion_time=router_metrics.get("avg_completion_time", 0.0),
            current_workload=router_metrics.get("current_workload", 0),
            reliability_score=validator_metrics.get("reliability_score", 0.5),
            task_distribution=task_distribution,
            collaboration_metrics=collaboration_metrics,
            error_rate=error_rate,
            avg_response_time=avg_response_time,
            knowledge_sharing_score=knowledge_sharing_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed metrics for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent status updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial status
        initial_status = await get_all_agents_status()
        await manager.send_personal_message(
            json.dumps({
                "type": "agent_status",
                "data": {k: v.dict() for k, v in initial_status.items()},
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for any message from client (heartbeat)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send periodic status update
                try:
                    current_status = await get_all_agents_status()
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "agent_status",
                            "data": {k: v.dict() for k, v in current_status.items()},
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                except Exception as e:
                    logger.error(f"Error sending status update: {e}")
                    break
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

async def _get_agent_status(agent_name: str, agent) -> AgentStatusResponse:
    """Helper function to get agent status"""
    try:
        # Initialize enhanced queue manager if not already done
        if not queue_manager.is_initialized:
            await queue_manager.initialize()
        
        # Determine agent status based on queue and recent activity
        queue_status = await queue_manager.get_queue_status(agent_name.lower())
        
        # Get performance metrics
        task_router = TaskRouter()
        validator = CrossAgentValidator()
        
        router_metrics = task_router.agent_performance.get(agent_name, {})
        validator_metrics = validator.agent_reliability.get(agent_name, {})
        
        # Determine current status
        if queue_status.get("status") == "not_initialized":
            status = "idle"
        elif queue_status.get("active_jobs", 0) > 0:
            status = "busy"
        elif queue_status.get("failed_jobs", 0) > 0:
            status = "error"
        else:
            status = "active"
        
        # Get current task if any
        current_task = None
        if queue_status.get("active_jobs", 0) > 0:
            current_task = f"Processing {queue_status.get('active_jobs')} tasks"
        
        performance_metrics = {
            "tasks_completed": router_metrics.get("tasks_completed", 0),
            "success_rate": router_metrics.get("success_rate", 0.0),
            "avg_completion_time": router_metrics.get("avg_completion_time", 0.0),
            "current_workload": router_metrics.get("current_workload", 0),
            "reliability_score": validator_metrics.get("reliability_score", 0.5)
        }
        
        # Get agent specializations
        specializations = []
        try:
            agent_specializations = await task_router.get_agent_specializations()
            if agent_name in agent_specializations:
                specializations = list(agent_specializations[agent_name])
        except Exception as e:
            logger.warning(f"Error getting specializations for {agent_name}: {e}")
        
        # Calculate collaboration score based on validator metrics
        collaboration_score = 0.0
        try:
            # Base collaboration score on reliability and success rate
            reliability = validator_metrics.get("reliability_score", 0.5)
            success_rate = router_metrics.get("success_rate", 0.0)
            collaboration_score = (reliability * 0.6) + (success_rate * 0.4)
            collaboration_score = min(1.0, max(0.0, collaboration_score))  # Ensure between 0 and 1
        except Exception as e:
            logger.warning(f"Error calculating collaboration score for {agent_name}: {e}")
        
        return AgentStatusResponse(
            agent_name=agent_name,
            status=status,
            current_task=current_task,
            last_activity=datetime.now().isoformat(),
            performance_metrics=performance_metrics,
            queue_status=queue_status,
            specializations=specializations,
            collaboration_score=collaboration_score
        )
        
    except Exception as e:
        logger.error(f"Error in _get_agent_status for {agent_name}: {e}")
        raise

# Event handler for real-time updates
async def _handle_agent_status_change(event_data: Dict[str, Any]):
    """Handle agent status change events and broadcast to WebSocket clients"""
    try:
        message = json.dumps({
            "type": "agent_status_change",
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        })
        await manager.broadcast(message)
    except Exception as e:
        logger.error(f"Error broadcasting agent status change: {e}")

@router.get("/network", response_model=AgentNetwork)
async def get_agent_network() -> AgentNetwork:
    """Get the network of relationships between agents"""
    try:
        orchestrator = AgentOrchestrator()
        task_router = TaskRouter()
        
        # Get all agent names
        agent_names = list(orchestrator.agents.keys())
        
        # Get task history to calculate relationships
        task_history = task_router.task_history
        
        # Calculate relationships between agents
        relationships = []
        relationship_data = {}
        
        # Initialize relationship data structure
        for agent1 in agent_names:
            for agent2 in agent_names:
                if agent1 < agent2:  # Avoid duplicates
                    key = f"{agent1}_{agent2}"
                    relationship_data[key] = {
                        "source_agent": agent1,
                        "target_agent": agent2,
                        "task_count": 0,
                        "successful_tasks": 0,
                        "last_interaction": None
                    }
        
        # Analyze task history to build relationships
        for task in task_history:
            agents_involved = task.get("agents", [])
            timestamp = task.get("timestamp", datetime.now().isoformat())
            outcome = task.get("outcome", "pending")
            
            # For each pair of agents involved in this task
            for i, agent1 in enumerate(agents_involved):
                for j, agent2 in enumerate(agents_involved):
                    if agent1 < agent2:  # Avoid duplicates
                        key = f"{agent1}_{agent2}"
                        if key in relationship_data:
                            relationship_data[key]["task_count"] += 1
                            if outcome == "success":
                                relationship_data[key]["successful_tasks"] += 1
                            
                            # Update last interaction if more recent
                            if (relationship_data[key]["last_interaction"] is None or 
                                timestamp > relationship_data[key]["last_interaction"]):
                                relationship_data[key]["last_interaction"] = timestamp
        
        # Convert relationship data to AgentRelationship objects
        for key, data in relationship_data.items():
            if data["task_count"] > 0:  # Only include relationships with interactions
                success_rate = data["successful_tasks"] / data["task_count"] if data["task_count"] > 0 else 0
                strength = 0.3 + (0.7 * success_rate)  # Base strength of 0.3 plus success rate influence
                
                relationships.append(AgentRelationship(
                    source_agent=data["source_agent"],
                    target_agent=data["target_agent"],
                    strength=strength,
                    task_count=data["task_count"],
                    success_rate=success_rate,
                    last_interaction=data["last_interaction"] or datetime.now().isoformat()
                ))
        
        return AgentNetwork(
            nodes=agent_names,
            relationships=relationships
        )
        
    except Exception as e:
        logger.error(f"Error getting agent network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specializations", response_model=Dict[str, List[str]])
async def get_agent_specializations() -> Dict[str, List[str]]:
    """Get specializations for all agents"""
    try:
        task_router = TaskRouter()
        specializations = await task_router.get_agent_specializations()
        
        # Convert sets to lists for JSON serialization
        return {agent: list(specs) for agent, specs in specializations.items()}
        
    except Exception as e:
        logger.error(f"Error getting agent specializations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workloads", response_model=Dict[str, int])
async def get_agent_workloads() -> Dict[str, int]:
    """Get current workload for all agents"""
    try:
        task_router = TaskRouter()
        return await task_router.get_agent_workloads()
        
    except Exception as e:
        logger.error(f"Error getting agent workloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-history", response_model=Dict[str, Any])
async def get_performance_history(
    days: int = Query(7, description="Number of days of history to retrieve")
) -> Dict[str, Any]:
    """Get historical performance metrics for all agents"""
    try:
        # This is a placeholder implementation
        # In a real implementation, we would retrieve historical data from a database
        
        orchestrator = AgentOrchestrator()
        task_router = TaskRouter()
        
        # Get all agent names
        agent_names = list(orchestrator.agents.keys())
        
        # Generate dates for the requested period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                      for i in range(days + 1)]
        
        # Generate placeholder data for each agent
        performance_history = {}
        for agent_name in agent_names:
            # Get current metrics as a baseline
            current_metrics = task_router.agent_performance.get(agent_name, {})
            base_success_rate = current_metrics.get("success_rate", 0.8)
            base_completion_time = current_metrics.get("avg_completion_time", 150)
            
            # Generate slightly varying metrics for each day
            daily_metrics = []
            for i, date in enumerate(date_range):
                # Vary metrics slightly each day (this is just for demonstration)
                variation = (i - days/2) / days  # -0.5 to 0.5 range
                success_rate = max(0, min(1, base_success_rate + variation * 0.2))
                completion_time = max(50, base_completion_time + variation * 30)
                
                daily_metrics.append({
                    "date": date,
                    "tasks_completed": int(5 + i * 2 + variation * 10),
                    "success_rate": success_rate,
                    "avg_completion_time": completion_time,
                    "workload": int(3 + variation * 5)
                })
            
            performance_history[agent_name] = daily_metrics
        
        return {
            "date_range": date_range,
            "performance_history": performance_history
        }
        
    except Exception as e:
        logger.error(f"Error getting performance history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Subscribe to relevant events
event_bus.subscribe("agent_task_started", _handle_agent_status_change)
event_bus.subscribe("agent_task_completed", _handle_agent_status_change)
event_bus.subscribe("agent_task_failed", _handle_agent_status_change)