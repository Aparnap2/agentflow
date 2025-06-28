"""
LangGraph-based agent implementation following PRD specifications
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from loguru import logger

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager


class AgentState(TypedDict):
    """State structure for LangGraph agents"""
    messages: List[BaseMessage]
    task: Dict[str, Any]
    context: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    requires_approval: bool
    agent_name: str
    retry_count: int


class LangGraphAgent:
    """Base LangGraph agent following PRD specifications"""
    
    def __init__(self, name: str, role: str, memory_manager: MemoryManager, 
                 approval_manager: ApprovalManager, personality: Dict[str, Any]):
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.personality = personality
        
        # Initialize OpenRouter LLM
        self.llm = ChatOpenAI(
            model=personality.get("model", "deepseek/deepseek-chat:free"),
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=self._get_openrouter_key(),
            temperature=personality.get("temperature", 0.7),
            max_tokens=personality.get("max_tokens", 2000)
        )
        
        # Agent-specific tools (to be overridden)
        self.tools = []
        
        logger.info(f"Initialized LangGraph agent: {name}")
    
    def _get_openrouter_key(self) -> str:
        """Get OpenRouter API key from environment"""
        import os
        return os.getenv("OPENROUTER_API_KEY", "")
    
    def _get_system_prompt(self) -> str:
        """Get agent's system prompt based on personality"""
        return f"""You are {self.name}, a {self.role} in a virtual AI office.

Your personality traits:
- Tone: {self.personality.get('tone', 'professional')}
- Focus: {self.personality.get('focus', 'task completion')}
- Expertise: {', '.join(self.personality.get('expertise', []))}

Your role is to {self.personality.get('description', 'complete assigned tasks effectively')}.

Always provide structured, actionable outputs that other agents can build upon.
Be thorough but concise. If you're uncertain, indicate your confidence level.
"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute agent-specific actions - to be overridden"""
        return {"message": "No specific actions implemented"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role,
            "status": "idle",
            "current_task": None,
            "outputs_ready": False
        }
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent workflow"""
        try:
            # Get shared context
            context = await self.memory_manager.get_shared_context()
            
            # Create state
            state = {
                "task": task,
                "context": context,
                "outputs": {}
            }
            
            # Execute actions
            action_results = await self._execute_actions(state)
            
            # Calculate confidence
            confidence = 0.8 if action_results else 0.5
            
            # Store results
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_output",
                content=action_results,
                is_shared=True,
                confidence=confidence,
                metadata={"task_id": task.get("id")}
            )
            
            return {
                "status": "completed",
                "output": action_results,
                "confidence": confidence,
                "requires_approval": confidence < 0.6,
                "agent": self.name,
                "task_id": task.get("id"),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{self.name} execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "task_id": task.get("id")
            }