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
        self.streamlined_architecture = {
            "total_agents": len(agents),
            "consolidated_capabilities": {
                "Manager": ["Product", "Workflow", "Operations", "Assistant"],
                "Marketing": ["Amplifier"],
                "Sales": ["Closer"]
            },
            "removed_agents": ["Product", "Amplifier", "Closer", "Assistant", "Workflow", "Operations"]
        }
    
    async def auto_execute_project(self, project_vision: str) -> str:
        """Auto-execute entire project with streamlined agent coordination"""
        execution_id = f"streamlined_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_status = "running"
        
        logger.info(f"🚀 Starting streamlined auto-execution: {execution_id}")
        self._log("system", "streamlined_execution_started", {
            "execution_id": execution_id,
            "architecture": "7_agents_with_consolidated_capabilities",
            "available_agents": list(self.agents.keys())
        })
        
        try:
            # Step 1: Manager auto-assigns tasks
            manager_result = await self._manager_auto_assign(project_vision)
            
            # Step 2: Execute agents with coordination
            await self._coordinated_execution(manager_result)
            
            self.current_status = "completed"
            self._log("system", "streamlined_execution_completed", {
                "execution_id": execution_id,
                "agents_executed": len(self.agents),
                "consolidated_capabilities_used": True
            })
            
            return execution_id
            
        except Exception as e:
            self.current_status = "error"
            self._log("system", "streamlined_execution_failed", {
                "error": str(e),
                "agents_available": len(self.agents),
                "architecture": "streamlined_7_agents"
            })
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
        """Execute agents in coordinated sequence (optimized for streamlined agents)"""
        # Phase 1: Independent agents
        await self._execute_agent_with_coordination("Legal", {})
        await self._execute_agent_with_coordination("Money", {})
        
        # Phase 2: Finance (needs Manager context for business insights)
        manager_context = await self._get_agent_context("Manager")
        await self._execute_agent_with_coordination("Finance", {"business_insights": manager_context})
        
        # Phase 3: Marketing (needs Finance context)
        finance_context = await self._get_agent_context("Finance")
        await self._execute_agent_with_coordination("Marketing", {
            "business_insights": manager_context,
            "finance_insights": finance_context
        })
        
        # Phase 4: Sales (needs Marketing + Finance context)
        if "Sales" in self.agents:
            marketing_context = await self._get_agent_context("Marketing")
            await self._execute_agent_with_coordination("Sales", {
                "finance_insights": finance_context,
                "marketing_insights": marketing_context
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
    
    def _get_agent_for_task(self, task_type: str) -> str:
        """Get appropriate agent for task type with streamlined 7-agent architecture"""
        agent_mapping = {
            # Redistributed tasks from removed agents to streamlined agents
            "product_analysis": "Manager",  # Manager handles Product capabilities
            "mvp_definition": "Manager",  # Manager handles Product capabilities
            "user_personas": "Manager",  # Manager handles Product capabilities
            "content_strategy": "Marketing",  # Marketing handles core content
            "brand_amplification": "Marketing",  # Marketing handles Amplifier capabilities
            "content_amplification": "Marketing",  # Marketing handles Amplifier capabilities
            "viral_marketing": "Marketing",  # Marketing handles Amplifier capabilities
            "sales_intelligence": "Sales",  # Sales handles core sales
            "lead_qualification": "Sales",  # Sales handles Closer capabilities
            "deal_closing": "Sales",  # Sales handles Closer capabilities
            "closing_strategy": "Sales",  # Sales handles Closer capabilities
            "administrative": "Manager",  # Manager handles Assistant tasks
            "executive_tasks": "Manager",  # Manager handles Assistant tasks
            "process_documentation": "Manager",  # Manager handles Workflow capabilities
            "workflow_optimization": "Manager",  # Manager handles Workflow capabilities
            "operations": "Manager",  # Manager handles Operations tasks
            "operational_processes": "Manager",  # Manager handles Operations tasks
            
            # Core streamlined agent tasks
            "financial_planning": "Finance",
            "financial_modeling": "Finance",
            "financial_operations": "Money",
            "payment_processing": "Money",
            "legal_compliance": "Legal",
            "legal_documentation": "Legal",
            "marketing_strategy": "Marketing",
            "seo_optimization": "Marketing",
            "sales_strategy": "Sales",
            "revenue_forecasting": "Sales",
            "vision_strategy": "Cofounder",
            "business_strategy": "Cofounder",
            "project_management": "Manager",
            "task_coordination": "Manager"
        }
        
        return agent_mapping.get(task_type, "Manager")  # Default to Manager for unknown tasks

    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            "status": self.current_status,
            "log_entries": len(self.execution_log),
            "recent_logs": self.execution_log[-10:] if self.execution_log else [],
            "last_updated": datetime.now().isoformat(),
            "available_agents": list(self.agents.keys())
        }