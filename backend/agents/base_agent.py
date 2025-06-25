from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
from datetime import datetime
from loguru import logger

from memory.graph_memory import GraphMemory
from memory.vector_memory import VectorMemory
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
    
    def __init__(self, name: str, role: str, personality: Dict[str, Any]):
        self.name = name
        self.role = role
        self.personality = personality
        self.status = AgentStatus.IDLE
        self.confidence_threshold = personality.get("confidence_threshold", 0.8)
        self.retry_limit = personality.get("retry_limit", 3)
        self.current_task = None
        self.outputs = {}
        
        # Memory systems
        self.graph_memory = GraphMemory()
        self.vector_memory = VectorMemory()
        
        # Tools
        self.tools = ToolRegistry(agent_name=name)
        
        logger.info(f"Initialized {name} agent with role: {role}")
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process assigned task - implemented by each agent"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get agent's system prompt based on personality"""
        pass
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method with error handling and retries"""
        self.current_task = task
        self.status = AgentStatus.THINKING
        
        for attempt in range(self.retry_limit):
            try:
                logger.info(f"{self.name} starting task attempt {attempt + 1}")
                
                # Process the task
                result = await self.process_task(task)
                
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
        """Store result in both private and shared memory"""
        # Private memory - detailed result
        await self.graph_memory.write_private_memory(
            agent_name=self.name,
            memory_type="task_result",
            content=result
        )
        
        # Shared memory - key outputs only
        if "output" in result:
            await self.graph_memory.write_shared_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_output",
                content=result["output"],
                confidence=result.get("confidence", 1.0)
            )
        
        # Vector memory - for semantic search
        if "summary" in result:
            await self.vector_memory.store_document(
                text=result["summary"],
                metadata={
                    "type": "agent_output",
                    "timestamp": datetime.now().isoformat(),
                    "task_id": self.current_task.get("id")
                },
                agent=self.name
            )
    
    async def _request_approval(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Request human approval for low-confidence results"""
        from approvals.approval_manager import ApprovalManager
        
        approval_manager = ApprovalManager()
        approval_id = await approval_manager.create_approval_request(
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
    
    async def get_context(self, context_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relevant context from shared memory"""
        return await self.graph_memory.query_shared_memory(
            memory_type=context_type,
            min_confidence=0.6
        )
    
    async def search_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search semantic knowledge base"""
        return await self.vector_memory.semantic_search(
            query=query,
            limit=limit
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