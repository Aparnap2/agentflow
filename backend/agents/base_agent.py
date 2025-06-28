from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
from datetime import datetime
from loguru import logger

from memory.memory_manager import MemoryManager
from tools.tool_registry import ToolRegistry

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    ERROR = "error"

class BaseAgent(ABC):
    """Base class for all AgentFlow agents"""
    
    def __init__(self, name: str, role: str, memory_manager: MemoryManager, approval_manager, personality: Optional[Dict[str, Any]] = None):
        self.name = name
        self.role = role
        self.personality = personality or {}
        self.status = AgentStatus.IDLE
        self.confidence_threshold = self.personality.get("confidence_threshold", 0.8)
        self.retry_limit = self.personality.get("retry_limit", 3)
        self.current_task = None
        self.outputs = {}
        
        # Memory and approval systems
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        
        # Tools - to be initialized by subclasses
        self.tools = []
        
        logger.info(f"Initialized {name} agent with role: {role}")
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process assigned task - implemented by each agent"""
        pass
    
    def get_system_prompt(self) -> str:
        """Get agent's system prompt based on personality"""
        return f"You are {self.name}, a {self.role}. {self.personality.get('description', '')}"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method with error handling and retries"""
        self.current_task = task
        self.status = AgentStatus.THINKING
        
        for attempt in range(self.retry_limit):
            try:
                logger.info(f"{self.name} starting task attempt {attempt + 1}")
                
                # Process the task
                result = await self.process_task(task) # process_task will use self.tools._arun
                
                # Check confidence
                confidence = result.get("confidence", 1.0)
                if confidence < self.confidence_threshold:
                    self.status = AgentStatus.WAITING_APPROVAL
                    logger.warning(f"{self.name} low confidence ({confidence}), requesting approval")
                    return await self._request_approval(result)
                
                # Store successful result
                await self._store_result(result)
                self.status = AgentStatus.COMPLETED
                self.outputs = result
                
                logger.info(f"{self.name} completed task successfully")
                return result
                
            except Exception as e:
                logger.error(f"{self.name} attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_limit - 1:
                    self.status = AgentStatus.ERROR
                    return {"error": str(e), "agent": self.name}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _store_result(self, result: Dict[str, Any]):
        """Store result in memory systems"""
        # Store detailed result in private memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="task_result",
            content=result,
            is_shared=False
        )
        
        # Store key outputs in shared memory
        if "output" in result:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_output",
                content=result["output"],
                is_shared=True,
                confidence=result.get("confidence", 1.0),
                metadata={
                    "task_id": self.current_task.get("id"),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _request_approval(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Request human approval for low-confidence results"""
        approval_id = await self.approval_manager.create_approval_request(
            agent_name=self.name,
            action_type="task_completion",
            content=result,
            reason=f"Low confidence: {result.get('confidence', 0)}"
        )
        
        return {
            "status": "pending_approval",
            "approval_id": approval_id,
            "result": result
        }
    
    async def _get_shared_context(self) -> Dict[str, Any]:
        """Get current shared context for this agent"""
        return await self.memory_manager.get_shared_context()
    
    async def _search_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search semantic knowledge base"""
        return await self.memory_manager.semantic_search(
            query=query,
            agent_name=self.name,
            limit=limit
        )
    
    async def _log_error(self, message: str):
        """Log error message"""
        logger.error(f"{self.name}: {message}")
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="error_log",
            content={"message": message, "timestamp": datetime.now().isoformat()},
            is_shared=False
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "current_task": self.current_task.get("id") if self.current_task else None,
            "outputs_ready": bool(self.outputs)
        }