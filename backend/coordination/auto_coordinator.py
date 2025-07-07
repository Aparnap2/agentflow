"""
Simple Agent Auto-Coordination System
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

class AutoCoordinator:
    def __init__(self, agents: Dict[str, Any], memory_manager):
        self.agents = agents
        self.memory_manager = memory_manager
        self.execution_log = []
        self.current_status = "idle"
    
    async def auto_execute_project(self, project_vision: str) -> str:
        """Auto-execute entire project with agent coordination"""
        execution_id = f"auto_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_status = "running"
        
        logger.info(f"🚀 Starting auto-execution: {execution_id}")
        self._log("system", "auto_execution_started", {"execution_id": execution_id})
        
        try:
            # Step 1: Manager auto-assigns tasks
            manager_result = await self._manager_auto_assign(project_vision)
            
            # Step 2: Execute agents with coordination
            await self._coordinated_execution(manager_result)
            
            self.current_status = "completed"
            self._log("system", "auto_execution_completed", {"execution_id": execution_id})
            
            return execution_id
            
        except Exception as e:
            self.current_status = "error"
            self._log("system", "auto_execution_failed", {"error": str(e)})
            raise
    
    async def _manager_auto_assign(self, vision: str) -> Dict[str, Any]:
        """Manager automatically creates task assignments"""
        self._log("Manager", "analyzing_vision", {"vision_length": len(vision)})
        
        manager = self.agents.get("Manager")
        task = {
            "id": f"auto_assign_{datetime.now().strftime('%H%M%S')}",
            "vision": vision,
            "mode": "auto_coordination"
        }
        
        result = await manager.execute(task)
        self._log("Manager", "task_assignment_complete", {"confidence": result.get("confidence", 0)})
        
        return result
    
    async def _coordinated_execution(self, manager_result: Dict[str, Any]):
        """Execute agents in coordinated sequence"""
        # Phase 1: Independent agents
        await self._execute_agent_with_coordination("Product", {})
        await self._execute_agent_with_coordination("Legal", {})
        
        # Phase 2: Finance (needs Product context)
        product_context = await self._get_agent_context("Product")
        await self._execute_agent_with_coordination("Finance", {"product_insights": product_context})
        
        # Phase 3: Marketing (needs Product + Finance context)
        finance_context = await self._get_agent_context("Finance")
        await self._execute_agent_with_coordination("Marketing", {
            "product_insights": product_context,
            "finance_insights": finance_context
        })
    
    async def _execute_agent_with_coordination(self, agent_name: str, peer_context: Dict[str, Any]):
        """Execute single agent with peer context"""
        self._log(agent_name, "execution_started", {"peer_context_keys": list(peer_context.keys())})
        
        agent = self.agents.get(agent_name)
        task = {
            "id": f"{agent_name.lower()}_{datetime.now().strftime('%H%M%S')}",
            "peer_context": peer_context,
            "coordination_mode": True
        }
        
        result = await agent.execute(task)
        self._log(agent_name, "execution_completed", {
            "confidence": result.get("confidence", 0),
            "output_size": len(str(result.get("output", {})))
        })
        
        return result
    
    async def _get_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Get agent's output for sharing with other agents"""
        try:
            memories = await self.memory_manager.get_agent_private_memory(agent_name, limit=1)
            if memories:
                return memories[0].get("content", {})
            return {}
        except:
            return {}
    
    def _log(self, agent: str, action: str, data: Dict[str, Any]):
        """Simple logging"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "data": data
        }
        self.execution_log.append(entry)
        logger.info(f"📋 [{agent}] {action}: {data}")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            "status": self.current_status,
            "log_entries": len(self.execution_log),
            "recent_logs": self.execution_log[-10:] if self.execution_log else [],
            "last_updated": datetime.now().isoformat()
        }