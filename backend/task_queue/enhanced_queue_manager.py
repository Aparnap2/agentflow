"""
Enhanced Queue Manager - Integrates queue manager with task processor
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from enum import Enum

from .queue_manager import queue_manager
from .task_processor import TaskProcessor

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class EnhancedQueueManager:
    """Enhanced queue manager with task processor integration"""
    
    def __init__(self):
        self.queue_manager = queue_manager
        self.task_processor = None
        self.is_initialized = False
        self._event_subscribers = {}
        self._cache = {}
    
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
        
    async def connect(self):
        """Connect to Redis"""
        if not self.queue_manager:
            logger.warning("Queue manager not initialized")
            return False
        return await self.queue_manager.connect()
    
    async def process_queue(self, queue_name: str, handler_func):
        """Process a queue with a handler function"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return False
            
        return await self.queue_manager.register_worker(queue_name, handler_func)
    
    def subscribe(self, event_type: str, callback):
        """Subscribe to queue events"""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(callback)
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to subscribers"""
        if event_type in self._event_subscribers:
            for callback in self._event_subscribers[event_type]:
                try:
                    await callback({"type": event_type, "data": data})
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")
    
    def _cache_get(self, key: str):
        """Get a value from the cache"""
        if key in self._cache:
            return self._cache[key]
        return None
    
    def _cache_set(self, key: str, value, ttl: int = 300):
        """Set a value in the cache with TTL"""
        self._cache[key] = value
        # In a real implementation, we would set up a timer to expire the cache
        # For simplicity, we're not implementing TTL expiration here
    
    async def get_task_result(self, task_id: str):
        """Get the result of a task"""
        if not self.is_initialized or not self.queue_manager.is_connected:
            logger.warning("Cannot get task result: Queue not initialized or connected")
            return None
            
        try:
            # Try to get from Redis
            result = await self.redis.hget(f"task_result:{task_id}", "result")
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            logger.error(f"Failed to get task result: {e}")
            return None
    
    async def get_system_metrics(self):
        """Get system-wide metrics"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
            
        try:
            queue_status = await self.queue_manager.get_all_queues_status()
            return {
                "queues": queue_status,
                "workers": len(self.queue_manager.workers),
                "is_connected": self.queue_manager.is_connected
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
queue_manager = EnhancedQueueManager()