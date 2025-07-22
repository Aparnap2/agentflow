"""
Agent factory for creating LangGraph-powered agents
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from agents.graph_agent import GraphAgent
from agents.personalities import get_agent_config
from agents.enhanced_manager_agent import EnhancedManagerAgent
from workflows.graph_orchestrator import GraphOrchestrator
from communication.event_bus import event_bus

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
    
    def create_agent(self, agent_type: str, enhanced: bool = False) -> GraphAgent:
        """Create a specific agent type
        
        Args:
            agent_type: Type of agent to create
            enhanced: Whether to create enhanced version of agent (if available)
        """
        # Get agent configuration
        agent_config = get_agent_config(agent_type)
        
        # Create agent based on type and enhanced flag
        if agent_type.lower() == "manager" and enhanced:
            # Create enhanced manager agent
            agent = EnhancedManagerAgent(
                memory_manager=self.memory_manager,
                approval_manager=self.approval_manager,
                event_bus=event_bus
            )
            logger.info(f"Created enhanced manager agent")
        else:
            # Create standard agent
            agent = GraphAgent(
                name=agent_type,
                role=self._get_agent_role(agent_type),
                memory_manager=self.memory_manager,
                approval_manager=self.approval_manager,
                personality=agent_config
            )
            logger.info(f"Created agent: {agent_type}")
        
        # Register agent
        self.agents[agent_type] = agent
        
        return agent
    
    def create_orchestrator(self, agent_types: Optional[List[str]] = None, use_enhanced_manager: bool = True) -> GraphOrchestrator:
        """Create an orchestrator with specified agents
        
        Args:
            agent_types: List of agent types to include in orchestrator
            use_enhanced_manager: Whether to use enhanced manager agent as orchestrator
        """
        # Default agent types
        if agent_types is None:
            agent_types = ["cofounder", "manager", "product", "finance", "marketing", "legal"]
        
        # Create any missing agents
        for agent_type in agent_types:
            if agent_type not in self.agents:
                # Use enhanced manager if requested
                if agent_type.lower() == "manager" and use_enhanced_manager:
                    self.create_agent(agent_type, enhanced=True)
                else:
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