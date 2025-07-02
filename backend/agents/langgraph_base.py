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
        
        # Initialize LLM configuration
        self.model = personality.get("model", "deepseek/deepseek-chat:free")
        self.api_key = self._get_api_key()
        self.temperature = personality.get("temperature", 0.7)
        self.max_tokens = personality.get("max_tokens", 2000)
        
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
            
            # Convert state to messages format for OpenRouter
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": json.dumps({
                    "task": task,
                    "context": context
                })}
            ]
            
            # Call LLM
            response = await self._call_llm(messages)
            response_content = response["choices"][0]["message"]["content"]
            
            # Try to parse JSON, fallback to structured text
            try:
                action_results = json.loads(response_content)
            except json.JSONDecodeError:
                # Create structured output from text response
                action_results = {
                    "analysis": response_content,
                    "agent": self.name,
                    "task_type": task.get("type", "general"),
                    "recommendations": ["Analysis completed"],
                    "confidence": 0.7
                }
            
            # Calculate confidence based on response
            confidence = float(response.get("choices", [{}])[0].get("finish_reason", "") == "stop") * 0.8
            
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