"""
Queue Manager - Redis-based queue system with BullMQ for task management
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from loguru import logger
import redis.asyncio as redis
from bullmq import Queue, Worker, Job, QueueEvents

class QueueManager:
    """Redis-based queue system with BullMQ for task management"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = None
        self.queues = {}
        self.workers = {}
        self.queue_events = {}
        self.job_handlers = {}
        self.is_connected = False
        self.is_initialized = False
        self.connection_attempts = 0
        self.max_connection_attempts = 3
    
    async def connect(self):
        """Connect to Redis"""
        if self.is_connected:
            return True
            
        try:
            self.redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            
            # Test connection
            await self.redis.ping()
            
            self.is_connected = True
            logger.info("Connected to Redis")
            return True
        except Exception as e:
            self.connection_attempts += 1
            logger.warning(f"Failed to connect to Redis (attempt {self.connection_attempts}/{self.max_connection_attempts}): {e}")
            
            if self.connection_attempts >= self.max_connection_attempts:
                logger.error("Max Redis connection attempts reached, using fallback mode")
                return False
                
            # Wait before retrying
            await asyncio.sleep(1)
            return await self.connect()
    
    async def initialize(self, connect_queue=True):
        """Initialize queue system"""
        if self.is_initialized:
            return True
            
        if connect_queue and not await self.connect():
            logger.warning("Queue system initialization skipped, using fallback mode")
            return False
        
        try:
            # Create standard queues
            standard_queues = [
                "content_tasks",
                "client_tasks",
                "finance_tasks",
                "research_tasks",
                "system_tasks"
            ]
            
            for queue_name in standard_queues:
                await self.create_queue(queue_name)
            
            self.is_initialized = True
            logger.info("Queue system initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize queue system: {e}")
            return False
    
    async def create_queue(self, queue_name: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new queue"""
        if not self.is_connected:
            logger.warning(f"Cannot create queue {queue_name}: Redis not connected")
            return False
            
        try:
            # Default options
            default_options = {
                "removeOnComplete": 100,  # Keep last 100 completed jobs
                "removeOnFail": 200,      # Keep last 200 failed jobs
                "defaultJobOptions": {
                    "attempts": 3,         # Retry failed jobs 3 times
                    "backoff": {
                        "type": "exponential",
                        "delay": 1000      # Start with 1 second delay
                    }
                }
            }
            
            # Merge with provided options
            queue_options = {**default_options, **(options or {})}
            
            # Create queue
            self.queues[queue_name] = Queue(
                queue_name,
                connection=self.redis,
                **queue_options
            )
            
            # Create queue events listener
            self.queue_events[queue_name] = QueueEvents(
                queue_name,
                connection=self.redis
            )
            
            logger.info(f"Created queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
            return False
    
    async def register_worker(self, queue_name: str, handler: Callable, concurrency: int = 1) -> bool:
        """Register a worker for a queue"""
        if not self.is_connected:
            logger.warning(f"Cannot register worker for {queue_name}: Redis not connected")
            return False
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot register worker for {queue_name}: Queue not found")
            return False
            
        try:
            # Store handler
            self.job_handlers[queue_name] = handler
            
            # Create worker
            self.workers[queue_name] = Worker(
                queue_name,
                self._process_job,
                connection=self.redis,
                concurrency=concurrency
            )
            
            logger.info(f"Registered worker for queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register worker for {queue_name}: {e}")
            return False
    
    async def add_job(self, queue_name: str, data: Dict[str, Any], job_id: Optional[str] = None,
                    options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Add a job to a queue"""
        if not self.is_connected:
            logger.warning(f"Cannot add job to {queue_name}: Redis not connected")
            return None
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot add job to {queue_name}: Queue not found")
            return None
            
        try:
            # Add job
            job = await self.queues[queue_name].add(
                data=data,
                jobId=job_id,
                opts=options
            )
            
            logger.info(f"Added job to {queue_name}: {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to add job to {queue_name}: {e}")
            return None
    
    async def get_job(self, queue_name: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details"""
        if not self.is_connected:
            logger.warning(f"Cannot get job {job_id}: Redis not connected")
            return None
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot get job {job_id}: Queue not found")
            return None
            
        try:
            # Get job
            job = await self.queues[queue_name].getJob(job_id)
            
            if not job:
                return None
                
            return {
                "id": job.id,
                "data": job.data,
                "status": await job.getState(),
                "progress": await job.getProgress(),
                "returnvalue": await job.getReturnvalue(),
                "failedReason": await job.getFailedReason(),
                "timestamp": job.timestamp,
                "processedOn": job.processedOn,
                "finishedOn": job.finishedOn,
                "attempts": job.attemptsMade
            }
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    async def get_queue_status(self, queue_name: str) -> Dict[str, Any]:
        """Get queue status"""
        if not self.is_connected:
            logger.warning(f"Cannot get status for {queue_name}: Redis not connected")
            return {"status": "disconnected"}
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot get status for {queue_name}: Queue not found")
            return {"status": "not_found"}
            
        try:
            # Get counts
            waiting = await self.queues[queue_name].count()
            active = await self.queues[queue_name].getActiveCount()
            completed = await self.queues[queue_name].getCompletedCount()
            failed = await self.queues[queue_name].getFailedCount()
            delayed = await self.queues[queue_name].getDelayedCount()
            
            return {
                "name": queue_name,
                "status": "active",
                "waiting": waiting,
                "active": active,
                "completed": completed,
                "failed": failed,
                "delayed": delayed,
                "total": waiting + active + completed + failed + delayed
            }
        except Exception as e:
            logger.error(f"Failed to get status for {queue_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_all_queues_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all queues"""
        if not self.is_connected:
            return {"status": "disconnected"}
            
        result = {}
        
        for queue_name in self.queues:
            result[queue_name] = await self.get_queue_status(queue_name)
            
        return result
    
    async def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue"""
        if not self.is_connected:
            logger.warning(f"Cannot pause {queue_name}: Redis not connected")
            return False
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot pause {queue_name}: Queue not found")
            return False
            
        try:
            await self.queues[queue_name].pause()
            logger.info(f"Paused queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause {queue_name}: {e}")
            return False
    
    async def resume_queue(self, queue_name: str) -> bool:
        """Resume a queue"""
        if not self.is_connected:
            logger.warning(f"Cannot resume {queue_name}: Redis not connected")
            return False
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot resume {queue_name}: Queue not found")
            return False
            
        try:
            await self.queues[queue_name].resume()
            logger.info(f"Resumed queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume {queue_name}: {e}")
            return False
    
    async def clear_queue(self, queue_name: str) -> bool:
        """Clear all jobs in a queue"""
        if not self.is_connected:
            logger.warning(f"Cannot clear {queue_name}: Redis not connected")
            return False
            
        if queue_name not in self.queues:
            logger.warning(f"Cannot clear {queue_name}: Queue not found")
            return False
            
        try:
            await self.queues[queue_name].obliterate()
            logger.info(f"Cleared queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear {queue_name}: {e}")
            return False
    
    async def stop_worker(self, queue_name: str) -> bool:
        """Stop a worker"""
        if queue_name not in self.workers:
            logger.warning(f"Cannot stop worker for {queue_name}: Worker not found")
            return False
            
        try:
            await self.workers[queue_name].close()
            del self.workers[queue_name]
            logger.info(f"Stopped worker for queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop worker for {queue_name}: {e}")
            return False
    
    async def stop_all(self) -> bool:
        """Stop all workers and close connections"""
        try:
            # Stop all workers
            for queue_name in list(self.workers.keys()):
                await self.stop_worker(queue_name)
            
            # Close Redis connection
            if self.redis:
                await self.redis.close()
                self.redis = None
                
            self.is_connected = False
            self.is_initialized = False
            
            logger.info("Stopped all queue workers and closed connections")
            return True
        except Exception as e:
            logger.error(f"Failed to stop queue system: {e}")
            return False
    
    async def _process_job(self, job: Job) -> Any:
        """Process a job using the registered handler"""
        queue_name = job.queueName
        
        if queue_name not in self.job_handlers:
            logger.warning(f"No handler registered for queue {queue_name}")
            return None
            
        try:
            # Call handler
            handler = self.job_handlers[queue_name]
            result = await handler(job)
            return result
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            raise

# Global instance
queue_manager = QueueManager()