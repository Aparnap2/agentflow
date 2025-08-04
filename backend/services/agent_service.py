"""
Reusable Agent Service Layer
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

class AgentService:
    def __init__(self, orchestrator, memory_manager):
        self.orchestrator = orchestrator
        self.memory = memory_manager
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get standardized agent status"""
        if agent_id not in self.orchestrator.agents:
            return {"error": f"Agent {agent_id} not found"}
        
        agent = self.orchestrator.agents[agent_id]
        status = agent.get_status()
        
        # Enhance with personality data
        from agents.personalities import get_agent_config
        personality = get_agent_config(agent_id)
        
        return {
            **status,
            **personality,
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status for all agents"""
        statuses = {}
        for agent_id in self.orchestrator.agents.keys():
            statuses[agent_id] = await self.get_agent_status(agent_id)
        return statuses
    
    async def execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task for specific agent"""
        try:
            result = await self.orchestrator.execute_single_agent(agent_id, task)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_agent_outputs(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get outputs from specific agent or all agents"""
        all_outputs = await self.orchestrator.get_outputs()
        
        if agent_id:
            return {k: v for k, v in all_outputs.items() 
                   if v.get('agent', '').lower() == agent_id.lower()}
        
        return all_outputs