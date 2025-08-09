"""
Enhanced Queue Manager - BullMQ-style Priority Queues per PRD
Implements priority queues, exponential backoff, and per-user quotas
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum

from .queue_manager import queue_manager
from .task_processor import TaskProcessor

class TaskPriority(str, Enum):
    """Task priority levels per PRD"""
    URGENT = "urgent"      # HITL approvals
    HIGH = "high"          # Customer-facing actions
    NORMAL = "normal"      # Standard operations
    LOW = "low"            # Background tasks
    BATCH = "batch"        # Bulk operations

class QueueType(str, Enum):
    """Queue types per PRD"""
    PRIORITY = "priority"      # Urgent approvals
    STANDARD = "standard"      # Normal operations
    BATCH = "batch"           # Bulk operations
    HITL = "hitl"            # Human-in-the-loop
    INSTAGRAM = "instagram"   # Instagram operations
    CRM = "crm"              # HubSpot CRM operations

class EnhancedQueueManager:
    """Enhanced queue manager with BullMQ-style priority queues per PRD"""
    
    def __init__(self):
        self.queue_manager = queue_manager
        self.task_processor = None
        self.is_initialized = False
        self._event_subscribers = {}
        self._cache = {}
        
        # PRD-specified queue configuration
        self.queue_config = {
            QueueType.PRIORITY: {
                "max_concurrency": 5,
                "retry_attempts": 3,
                "retry_delay": 1,  # seconds
                "priority_weight": 100
            },
            QueueType.STANDARD: {
                "max_concurrency": 10,
                "retry_attempts": 3,
                "retry_delay": 2,
                "priority_weight": 50
            },
            QueueType.BATCH: {
                "max_concurrency": 2,
                "retry_attempts": 2,
                "retry_delay": 5,
                "priority_weight": 10
            },
            QueueType.HITL: {
                "max_concurrency": 3,
                "retry_attempts": 1,  # HITL tasks shouldn't auto-retry
                "retry_delay": 0,
                "priority_weight": 200  # Highest priority
            },
            QueueType.INSTAGRAM: {
                "max_concurrency": 3,
                "retry_attempts": 2,
                "retry_delay": 10,  # Respect rate limits
                "priority_weight": 75
            },
            QueueType.CRM: {
                "max_concurrency": 5,
                "retry_attempts": 3,
                "retry_delay": 3,
                "priority_weight": 60
            }
        }
        
        # Per-user quotas per PRD
        self.user_quotas = {
            "default": {
                "requests_per_minute": 100,
                "requests_per_hour": 2000,
                "priority_requests_per_hour": 50
            }
        }
        
        # Rate limiting tracking
        self._rate_limits = {}
        
        # Exponential backoff configuration
        self.backoff_config = {
            "base_delay": 1,
            "max_delay": 300,  # 5 minutes
            "multiplier": 2,
            "jitter": True
        }
    
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
                     priority: Optional[str] = None, user_id: Optional[str] = None,
                     queue_type: Optional[str] = None) -> Optional[str]:
        """Add a task to the priority queue with rate limiting"""
        if not self.is_initialized:
            logger.warning("Enhanced queue manager not initialized")
            return None
        
        # Check rate limits
        if user_id and not await self._check_rate_limit(user_id, priority):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return None
        
        # Determine queue type and priority
        queue_type = queue_type or self._determine_queue_type(task_type)
        priority = priority or self._determine_priority(task_type, task_data)
        
        # Create enhanced task with metadata
        enhanced_task = {
            "id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id or 'system'}",
            "type": task_type,
            "data": task_data,
            "priority": priority,
            "queue_type": queue_type,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "attempts": 0,
            "max_attempts": self.queue_config[QueueType(queue_type)]["retry_attempts"],
            "retry_delay": self.queue_config[QueueType(queue_type)]["retry_delay"],
            "status": "pending"
        }
        
        # Add to appropriate queue with priority scoring
        priority_score = self._calculate_priority_score(priority, queue_type)
        
        try:
            # Store task in Redis with priority
            await self.redis.zadd(
                f"queue:{queue_type}",
                {json.dumps(enhanced_task): priority_score}
            )
            
            # Track in user rate limits
            if user_id:
                await self._track_user_request(user_id, priority)
            
            logger.info(f"Added task {enhanced_task['id']} to {queue_type} queue with priority {priority}")
            
            return enhanced_task["id"]
            
        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
            return None
    
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

    def _determine_queue_type(self, task_type: str) -> str:
        """Determine queue type based on task type"""
        queue_mapping = {
            "hitl_approval": QueueType.HITL.value,
            "instagram_post": QueueType.INSTAGRAM.value,
            "instagram_dm": QueueType.INSTAGRAM.value,
            "crm_update": QueueType.CRM.value,
            "hubspot_sync": QueueType.CRM.value,
            "batch_process": QueueType.BATCH.value,
            "urgent_notification": QueueType.PRIORITY.value
        }
        return queue_mapping.get(task_type, QueueType.STANDARD.value)
    
    def _determine_priority(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """Determine task priority based on type and data"""
        # HITL tasks are always urgent
        if task_type.startswith("hitl_"):
            return TaskPriority.URGENT.value
        
        # Customer-facing tasks are high priority
        if task_type in ["instagram_post", "instagram_dm", "customer_email"]:
            return TaskPriority.HIGH.value
        
        # Financial operations are high priority
        if task_type in ["invoice_generation", "payment_processing"]:
            return TaskPriority.HIGH.value
        
        # Check for explicit priority in task data
        if "priority" in task_data:
            return task_data["priority"]
        
        # Default to normal
        return TaskPriority.NORMAL.value
    
    def _calculate_priority_score(self, priority: str, queue_type: str) -> float:
        """Calculate priority score for Redis sorted set"""
        priority_scores = {
            TaskPriority.URGENT.value: 1000,
            TaskPriority.HIGH.value: 800,
            TaskPriority.NORMAL.value: 500,
            TaskPriority.LOW.value: 200,
            TaskPriority.BATCH.value: 100
        }
        
        base_score = priority_scores.get(priority, 500)
        queue_weight = self.queue_config[QueueType(queue_type)]["priority_weight"]
        
        # Higher score = higher priority (Redis ZREVRANGE for highest first)
        return base_score + queue_weight + datetime.now().timestamp()
    
    async def _check_rate_limit(self, user_id: str, priority: Optional[str] = None) -> bool:
        """Check if user is within rate limits"""
        now = datetime.now()
        minute_key = f"rate_limit:{user_id}:minute:{now.strftime('%Y%m%d_%H%M')}"
        hour_key = f"rate_limit:{user_id}:hour:{now.strftime('%Y%m%d_%H')}"
        
        quota = self.user_quotas.get(user_id, self.user_quotas["default"])
        
        try:
            # Check minute limit
            minute_count = await self.redis.get(minute_key) or 0
            if int(minute_count) >= quota["requests_per_minute"]:
                return False
            
            # Check hour limit
            hour_count = await self.redis.get(hour_key) or 0
            if int(hour_count) >= quota["requests_per_hour"]:
                return False
            
            # Check priority hour limit
            if priority == TaskPriority.URGENT.value:
                priority_hour_key = f"rate_limit:{user_id}:priority_hour:{now.strftime('%Y%m%d_%H')}"
                priority_count = await self.redis.get(priority_hour_key) or 0
                if int(priority_count) >= quota["priority_requests_per_hour"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def _track_user_request(self, user_id: str, priority: Optional[str] = None):
        """Track user request for rate limiting"""
        now = datetime.now()
        minute_key = f"rate_limit:{user_id}:minute:{now.strftime('%Y%m%d_%H%M')}"
        hour_key = f"rate_limit:{user_id}:hour:{now.strftime('%Y%m%d_%H')}"
        
        try:
            # Increment counters with expiration
            await self.redis.incr(minute_key)
            await self.redis.expire(minute_key, 60)
            
            await self.redis.incr(hour_key)
            await self.redis.expire(hour_key, 3600)
            
            # Track priority requests separately
            if priority == TaskPriority.URGENT.value:
                priority_hour_key = f"rate_limit:{user_id}:priority_hour:{now.strftime('%Y%m%d_%H')}"
                await self.redis.incr(priority_hour_key)
                await self.redis.expire(priority_hour_key, 3600)
                
        except Exception as e:
            logger.error(f"Failed to track user request: {e}")
    
    async def get_next_task(self, queue_type: str) -> Optional[Dict[str, Any]]:
        """Get next highest priority task from queue"""
        if not self.is_initialized:
            return None
        
        try:
            # Get highest priority task (ZREVRANGE for highest score first)
            result = await self.redis.zrevrange(f"queue:{queue_type}", 0, 0, withscores=True)
            
            if not result:
                return None
            
            task_json, score = result[0]
            task = json.loads(task_json)
            
            # Remove from queue
            await self.redis.zrem(f"queue:{queue_type}", task_json)
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return None
    
    async def retry_task_with_backoff(self, task: Dict[str, Any]) -> bool:
        """Retry task with exponential backoff"""
        task["attempts"] += 1
        
        if task["attempts"] >= task["max_attempts"]:
            logger.warning(f"Task {task['id']} exceeded max attempts")
            await self._move_to_dead_letter_queue(task)
            return False
        
        # Calculate backoff delay
        delay = self._calculate_backoff_delay(task["attempts"])
        
        # Schedule retry
        retry_time = datetime.now() + timedelta(seconds=delay)
        task["retry_at"] = retry_time.isoformat()
        task["status"] = "retrying"
        
        # Add to delayed queue
        await self.redis.zadd(
            f"queue:delayed:{task['queue_type']}",
            {json.dumps(task): retry_time.timestamp()}
        )
        
        logger.info(f"Scheduled retry for task {task['id']} in {delay} seconds")
        return True
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.backoff_config["base_delay"] * (
            self.backoff_config["multiplier"] ** (attempt - 1)
        )
        
        # Cap at max delay
        delay = min(delay, self.backoff_config["max_delay"])
        
        # Add jitter if enabled
        if self.backoff_config["jitter"]:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        return delay
    
    async def _move_to_dead_letter_queue(self, task: Dict[str, Any]):
        """Move failed task to dead letter queue"""
        task["status"] = "failed"
        task["failed_at"] = datetime.now().isoformat()
        
        await self.redis.lpush(
            f"queue:dead_letter:{task['queue_type']}",
            json.dumps(task)
        )
        
        logger.error(f"Moved task {task['id']} to dead letter queue")
    
    async def process_delayed_tasks(self):
        """Process delayed tasks that are ready for retry"""
        try:
            for queue_type in QueueType:
                delayed_queue = f"queue:delayed:{queue_type.value}"
                now = datetime.now().timestamp()
                
                # Get tasks ready for retry
                ready_tasks = await self.redis.zrangebyscore(
                    delayed_queue, 0, now, withscores=True
                )
                
                for task_json, score in ready_tasks:
                    task = json.loads(task_json)
                    
                    # Move back to main queue
                    priority_score = self._calculate_priority_score(
                        task["priority"], task["queue_type"]
                    )
                    
                    await self.redis.zadd(
                        f"queue:{task['queue_type']}",
                        {task_json: priority_score}
                    )
                    
                    # Remove from delayed queue
                    await self.redis.zrem(delayed_queue, task_json)
                    
                    logger.info(f"Moved delayed task {task['id']} back to main queue")
                    
        except Exception as e:
            logger.error(f"Failed to process delayed tasks: {e}")
    
    async def get_queue_metrics(self) -> Dict[str, Any]:
        """Get comprehensive queue metrics"""
        metrics = {
            "queues": {},
            "rate_limits": {},
            "system_health": "healthy",
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            for queue_type in QueueType:
                queue_name = f"queue:{queue_type.value}"
                delayed_queue = f"queue:delayed:{queue_type.value}"
                dead_letter_queue = f"queue:dead_letter:{queue_type.value}"
                
                metrics["queues"][queue_type.value] = {
                    "pending": await self.redis.zcard(queue_name),
                    "delayed": await self.redis.zcard(delayed_queue),
                    "failed": await self.redis.llen(dead_letter_queue),
                    "config": self.queue_config[queue_type]
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get queue metrics: {e}")
            return {"error": str(e)}
    
    async def set_user_quota(self, user_id: str, quota: Dict[str, int]):
        """Set custom quota for user"""
        self.user_quotas[user_id] = quota
        logger.info(f"Set custom quota for user {user_id}: {quota}")
    
    async def get_user_rate_limit_status(self, user_id: str) -> Dict[str, Any]:
        """Get current rate limit status for user"""
        now = datetime.now()
        minute_key = f"rate_limit:{user_id}:minute:{now.strftime('%Y%m%d_%H%M')}"
        hour_key = f"rate_limit:{user_id}:hour:{now.strftime('%Y%m%d_%H')}"
        priority_hour_key = f"rate_limit:{user_id}:priority_hour:{now.strftime('%Y%m%d_%H')}"
        
        try:
            quota = self.user_quotas.get(user_id, self.user_quotas["default"])
            
            minute_count = int(await self.redis.get(minute_key) or 0)
            hour_count = int(await self.redis.get(hour_key) or 0)
            priority_count = int(await self.redis.get(priority_hour_key) or 0)
            
            return {
                "user_id": user_id,
                "quota": quota,
                "current_usage": {
                    "requests_this_minute": minute_count,
                    "requests_this_hour": hour_count,
                    "priority_requests_this_hour": priority_count
                },
                "remaining": {
                    "requests_this_minute": max(0, quota["requests_per_minute"] - minute_count),
                    "requests_this_hour": max(0, quota["requests_per_hour"] - hour_count),
                    "priority_requests_this_hour": max(0, quota["priority_requests_per_hour"] - priority_count)
                },
                "rate_limited": (
                    minute_count >= quota["requests_per_minute"] or
                    hour_count >= quota["requests_per_hour"]
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"error": str(e)}
# Global instance
queue_manager = EnhancedQueueManager()