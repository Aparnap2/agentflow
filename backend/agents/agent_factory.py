"""
Agent factory for creating LangGraph-powered agents
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from agents.graph_agent import GraphAgent
from agents.personalities import get_agent_config
from workflows.graph_orchestrator import GraphOrchestrator

class AgentFactory:
    """Factory for creating LangGraph-powered agents"""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        approval_manager: ApprovalManager
    ):
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.agents = {}
    
    def create_agent(self, agent_type: str) -> GraphAgent:
        """Create a specific agent type"""
        # Get agent configuration
        agent_config = get_agent_config(agent_type)
        
        # Create agent
        agent = GraphAgent(
            name=agent_type,
            role=self._get_agent_role(agent_type),
            memory_manager=self.memory_manager,
            approval_manager=self.approval_manager,
            personality=agent_config
        )
        
        # Register agent
        self.agents[agent_type] = agent
        logger.info(f"Created agent: {agent_type}")
        
        return agent
    
    def create_orchestrator(self, agent_types: Optional[List[str]] = None) -> GraphOrchestrator:
        """Create an orchestrator with specified agents"""
        # Default agent types
        if agent_types is None:
            agent_types = ["cofounder", "manager", "product", "finance", "marketing", "legal"]
        
        # Create any missing agents
        for agent_type in agent_types:
            if agent_type not in self.agents:
                self.create_agent(agent_type)
        
        # Filter agents to include only requested types
        agents = {name: agent for name, agent in self.agents.items() if name in agent_types}
        
        # Create orchestrator
        orchestrator = GraphOrchestrator(
            memory_manager=self.memory_manager,
            approval_manager=self.approval_manager,
            agents=agents
        )
        
        logger.info(f"Created orchestrator with {len(agents)} agents")
        return orchestrator
    
    def _get_agent_role(self, agent_type: str) -> str:
        """Get role description for agent type"""
        roles = {
            "cofounder": "Vision & Strategy",
            "manager": "Project Management",
            "product": "Product Management",
            "finance": "Financial Planning",
            "marketing": "Content & Marketing",
            "legal": "Legal & Compliance",
            "sales": "Sales & Revenue",
            "operations": "Operations & Process",
            "assistant": "Executive Assistant",
            "closer": "Sales Intelligence & Closing",
            "amplifier": "Content & Brand",
            "money": "Financial Operations",
            "workflow": "Process & Systems"
        }
        
        return roles.get(agent_type.lower(), "Specialist")