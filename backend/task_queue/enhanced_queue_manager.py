"""
Enhanced Queue Manager - Integrates queue manager with task processor
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from .queue_manager import queue_manager
from .task_processor import TaskProcessor

class EnhancedQueueManager:
    """Enhanced queue manager with task processor integration"""
    
    def __init__(self):
        self.queue_manager = queue_manager
        self.task_processor = None
        self.is_initialized = False
    
    async def initialize(self, memory_manager=None, agents=None, workflow_manager=None, connect_queue=True):
        """Initialize enhanced queue manager"""
        if self.is_initialized:
            return True
            
        # Initialize queue manager
        queue_initialized = await self.queue_manager.initialize(connect_queue)
        
        # Initialize task processor
        self.task_processor = TaskProcessor(memory_manager, agents, workflow_manager)
        await self.task_processor.initialize()
        
        self.is_initialized = True
        logger.info("Enhanced queue manager initialized")
        return queue_initialized
    
    async def add_task(self, task_type: str, task_data: Dict[str, Any], 
                     priority: Optional[str] = None) -> Optional[str]:
        """Add a task to the queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return None
            
        return await self.task_processor.add_task(task_type, task_data, priority)
    
    async def get_task_status(self, queue_name: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return None
            
        return await self.task_processor.get_task_status(queue_name, job_id)
    
    async def get_queue_status(self, queue_name: str) -> Dict[str, Any]:
        """Get status of a queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return {"status": "not_initialized"}
            
        return await self.queue_manager.get_queue_status(queue_name)
    
    async def get_all_queues_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all queues"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return {"status": "not_initialized"}
            
        return await self.queue_manager.get_all_queues_status()
    
    async def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.queue_manager.pause_queue(queue_name)
    
    async def resume_queue(self, queue_name: str) -> bool:
        """Resume a queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.queue_manager.resume_queue(queue_name)
    
    async def clear_queue(self, queue_name: str) -> bool:
        """Clear all jobs in a queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.queue_manager.clear_queue(queue_name)
    
    async def register_handler(self, queue_name: str, handler_func, concurrency: int = 1) -> bool:
        """Register a handler for a queue"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.task_processor.register_handler(queue_name, handler_func, concurrency)
    
    async def stop_all(self) -> bool:
        """Stop all workers and close connections"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.queue_manager.stop_all()
    
    @property
    def redis(self):
        """Get Redis client"""
        return self.queue_manager.redis if self.queue_manager else None

# Global instance
queue_manager = EnhancedQueueManager()