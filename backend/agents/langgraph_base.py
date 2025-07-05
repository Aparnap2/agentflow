"""
LangGraph-based agent implementation following PRD specifications
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from tools.tool_registry import ToolRegistry
import aiohttp
from loguru import logger

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from agents.personalities import get_personality_prompt, get_agent_config


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
                 approval_manager: ApprovalManager, personality: Dict[str, Any] = None):
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        
        # Enhanced personality system
        self.personality_config = get_agent_config(name)
        self.personality = personality or self.personality_config
        
        # Initialize LLM configuration with personality
        self.model = self.personality.get("model", "deepseek/deepseek-chat:free")
        self.api_key = self._get_api_key()
        self.temperature = self.personality.get("temperature", 0.7)
        self.max_tokens = self.personality.get("max_tokens", 2000)
        self.confidence_threshold = self.personality.get("confidence_threshold", 0.7)
        
        # Agent-specific tools (to be overridden)
        self.tools = []
        
        self.tool_registry = ToolRegistry(self.name)
        logger.info(f"Initialized LangGraph agent: {name}")
    
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        import os
        # Try multiple API key sources
        return (
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("DEEPSEEK_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            ""
        )
    
    def _get_system_prompt(self) -> str:
        """Get agent's enhanced personality-driven system prompt"""
        return get_personality_prompt(self.name)
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute agent-specific actions - to be overridden"""
        return {"message": "No specific actions implemented"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status with personality info"""
        return {
            "name": self.name,
            "role": self.role,
            "personality_name": self.personality_config.get("name", self.name),
            "avatar_emoji": self.personality_config.get("avatar_emoji", "🤖"),
            "traits": self.personality_config.get("traits", []),
            "expertise_areas": self.personality_config.get("expertise_areas", []),
            "status": "idle",
            "current_task": None,
            "outputs_ready": False,
            "confidence_threshold": self.confidence_threshold
        }
    
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration"""
        if 'temperature' in config:
            self.personality['temperature'] = config['temperature']
            self.temperature = config['temperature']
        if 'confidenceThreshold' in config:
            self.personality['confidence_threshold'] = config['confidenceThreshold']
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Make a direct API call to OpenRouter/DeepSeek"""
        if not self.api_key:
            raise Exception("No API key configured")
            
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://agentflow.ai",
                    "X-Title": "AgentFlow"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {error_text}")
                return await response.json()

    def get_config(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        return {
            "approvalMode": "manual",
            "priority": "medium", 
            "temperature": self.personality.get('temperature', 0.7),
            "confidenceThreshold": self.personality.get('confidence_threshold', 0.8),
            "maxRetries": 3,
            "enabled": True
        }
    
    async def _select_dynamic_tools(self, task: Dict[str, Any], context: Dict[str, Any]) -> List[BaseTool]:
        """Select tools dynamically based on task and context"""
        selected_tools = []
        # Example dynamic tool selection logic
        if "market" in task.get("type", ""):
            # Add a mock real-time market data tool
            selected_tools.append(BaseTool())
        if "finance" in task.get("type", ""):
            # Add a mock financial analysis tool
            selected_tools.append(BaseTool())
        return selected_tools

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent workflow with proper memory integration"""
        try:
            # Get shared context from Qdrant (global)
            shared_context = await self.memory_manager.get_shared_context()
            
            # Get agent's private memory from Neo4j (personalized)
            private_memory = await self.memory_manager.get_agent_private_memory(self.name)
            
            # Combine contexts
            context = {
                "shared_context": shared_context,
                "private_memory": private_memory,
                "agent_expertise": self.personality.get("expertise_areas", []),
                "previous_outputs": await self._get_previous_outputs()
            }
            
            # Create state
            state = {
                "task": task,
                "context": context,
                "outputs": {}
            }
            
            # Execute agent-specific actions
            action_results = await self._execute_actions(state)
            
            # Calculate confidence
            confidence = self._calculate_confidence(action_results)
            
            # Store in both memory systems
            await self._store_in_memory_systems(task, action_results, confidence)
            
            return {
                "status": "completed",
                "output": action_results,
                "confidence": confidence,
                "requires_approval": confidence < self.confidence_threshold,
                "agent": self.name,
                "task_id": task.get("id"),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{self.name} execution failed: {str(e)}")
            # Store error in private memory
            await self.memory_manager.store_agent_private_memory(
                agent_name=self.name,
                memory_type="error_log",
                content={"error": str(e), "task": task, "timestamp": datetime.now().isoformat()}
            )
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "task_id": task.get("id")
            }
    
    async def _get_previous_outputs(self) -> List[Dict[str, Any]]:
        """Get agent's previous outputs from memory"""
        try:
            return await self.memory_manager.get_agent_private_memory(self.name, memory_type="outputs")
        except:
            return []
    
    def _calculate_confidence(self, outputs: Dict[str, Any]) -> float:
        """Calculate confidence based on output completeness"""
        base_confidence = 0.7
        
        # Check output completeness
        if isinstance(outputs, dict):
            if len(outputs) > 3:  # Has multiple sections
                base_confidence += 0.1
            if "recommendations" in outputs or "next_steps" in outputs:
                base_confidence += 0.1
            if "analysis" in outputs or "strategy" in outputs:
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    async def _think(self, prompt: str) -> Dict[str, Any]:
        """Core thinking method using LLM"""
        try:
            import aiohttp
            import os
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return {"error": "No API key", "fallback": True}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"You are {self.name}, expert in {self.role}. Think deeply and provide structured insights."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.temperature
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        try:
                            import json
                            return json.loads(content)
                        except:
                            return {"insights": content, "confidence": 0.7}
                    else:
                        return {"error": "API call failed", "fallback": True}
        except Exception as e:
            return {"error": str(e), "fallback": True}
    
    async def _store_in_memory_systems(self, task: Dict[str, Any], results: Dict[str, Any], confidence: float):
        """Store results in both Neo4j (private) and Qdrant (shared)"""
        # Store in private memory (Neo4j) - agent's personal context
        await self.memory_manager.store_agent_private_memory(
            agent_name=self.name,
            memory_type=f"{self.name.lower()}_task",
            content={
                "task": task,
                "results": results,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "task_type": task.get("type", "general")
            }
        )
        
        # Store in shared memory (Qdrant) - global context for other agents
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type=f"{self.name.lower()}_output",
            content=results,
            is_shared=True,
            confidence=confidence,
            metadata={"task_id": task.get("id"), "agent": self.name}
        )
    
    async def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle conversation chat - to be overridden by specific agents"""
        try:
            # Get context
            context = await self.memory_manager.get_shared_context()
            
            # Create simple task for chat
            task = {
                "id": conversation_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": "conversation",
                "message": message
            }
            
            # Execute the chat
            result = await self.execute(task)
            
            if result.get("status") == "completed":
                return result.get("output", {"message": "Chat completed successfully"})
            else:
                return {"message": "I'm here to help! Please tell me more about what you need."}
                
        except Exception as e:
            logger.error(f"Chat failed for {self.name}: {e}")
            return {"message": "I apologize for the error. Please try again."}