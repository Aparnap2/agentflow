"""
LangGraph workflow integration for AgentFlow
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from loguru import logger
from events.event_bus import event_bus
from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from core.agent_factory import AgentFactory
from core.langgraph_core import GraphOrchestrator

class LangGraphWorkflow:
    """Main LangGraph workflow integration for AgentFlow"""
    
    def __init__(self, memory_manager: MemoryManager, approval_manager: ApprovalManager):
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.factory = None
        self.active_workflows = {}
        
    async def _get_factory(self):
        """Get or initialize agent factory"""
        if self.factory is None:
            self.factory = AgentFactory(self.memory_manager, self.approval_manager)
        return self.factory
    
    async def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Create a new workflow instance"""
        # Generate workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get agent types from config
        agent_types = workflow_config.get("agents", ["cofounder", "manager", "product", "finance", "marketing", "legal"])
        
        # Get factory and create orchestrator
        factory = await self._get_factory()
        orchestrator = factory.create_orchestrator(agent_types)
        
        # Store workflow
        self.active_workflows[workflow_id] = {
            "orchestrator": orchestrator,
            "config": workflow_config,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created workflow {workflow_id} with {len(agent_types)} agents")
        
        # Broadcast event
        await event_bus.broadcast_update("workflow_created", {
            "workflow_id": workflow_id,
            "agents": agent_types,
            "created_at": datetime.now().isoformat()
        })
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow by ID"""
        # Get workflow
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return {"status": "error", "error": "Workflow not found"}
        
        # Get orchestrator
        orchestrator = workflow["orchestrator"]
        
        # Update status
        workflow["status"] = "running"
        workflow["started_at"] = datetime.now().isoformat()
        
        # Broadcast event
        await event_bus.broadcast_update("workflow_started", {
            "workflow_id": workflow_id,
            "started_at": workflow["started_at"]
        })
        
        try:
            # Prepare initial state
            initial_state = {
                "project_vision": workflow["config"].get("vision", ""),
                "shared_context": workflow["config"].get("context", {})
            }
            
            # Execute workflow
            logger.info(f"Executing workflow {workflow_id}")
            result = await orchestrator.execute_workflow(initial_state)
            
            # Update workflow status
            workflow["status"] = "completed"
            workflow["completed_at"] = datetime.now().isoformat()
            workflow["result"] = result
            
            # Broadcast event
            await event_bus.broadcast_update("workflow_completed", {
                "workflow_id": workflow_id,
                "status": "completed",
                "completed_at": workflow["completed_at"],
                "agents_completed": list(result.get("agent_outputs", {}).keys())
            })
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            
            # Update workflow status
            workflow["status"] = "error"
            workflow["error"] = str(e)
            
            # Broadcast event
            await event_bus.broadcast_update("workflow_error", {
                "workflow_id": workflow_id,
                "error": str(e)
            })
            
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {"status": "not_found"}
        
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "created_at": workflow.get("created_at"),
            "started_at": workflow.get("started_at"),
            "completed_at": workflow.get("completed_at"),
            "agents": workflow["config"].get("agents", []),
            "has_result": "result" in workflow
        }
    
    async def get_workflow_result(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow result"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {"status": "not_found"}
        
        if "result" not in workflow:
            return {"status": workflow["status"], "result": None}
        
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "result": workflow["result"]
        }
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {"status": "not_found"}
        
        if workflow["status"] != "running":
            return {"status": workflow["status"], "message": "Workflow is not running"}
        
        # Update status
        workflow["status"] = "cancelled"
        workflow["cancelled_at"] = datetime.now().isoformat()
        
        # Broadcast event
        await event_bus.broadcast_update("workflow_cancelled", {
            "workflow_id": workflow_id,
            "cancelled_at": workflow["cancelled_at"]
        })
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled"
        }
    
    async def chat_with_agent(self, agent_type: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with a specific agent"""
        # Create session ID if not provided
        if not session_id:
            session_id = f"chat_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get factory and create agent
        factory = await self._get_factory()
        agent = factory.create_agent(agent_type)
        
        # Create task for agent
        task = {
            "type": "chat",
            "message": message,
            "session_id": session_id
        }
        
        # Execute agent
        result = await agent.execute(task)
        
        return {
            "session_id": session_id,
            "agent": agent_type,
            "message": result.get("output", {}).get("response", "No response generated"),
            "confidence": result.get("confidence", 0.7)
        }