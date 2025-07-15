"""
Enhanced Queue Manager with Redis, Bull-like functionality for AgentFlow
Supports batching, real-time updates, and agent coordination
"""
import asyncio
import json
import uuid
import time
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger

# Import Upstash Redis instead of standard Redis
try:
    from upstash_redis import Redis
    from upstash_redis.asyncio import Redis as AsyncRedis
    USING_UPSTASH = True
except ImportError:
    import redis.asyncio as redis
    USING_UPSTASH = False

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class QueueTask:
    id: str
    queue_name: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    retry_count: int = 0
    max_retries: int = 3
    delay_ms: int = 0
    agent_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

@dataclass
class BatchUpdate:
    batch_id: str
    updates: List[Dict[str, Any]]
    created_at: datetime
    processed: bool = False

class EnhancedQueueManager:
    def __init__(self):
        # Handle Upstash Redis URL format
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_token = os.getenv("REDIS_TOKEN")
        
        # For Upstash Redis, use token-based authentication
        if redis_token and "upstash.io" in redis_url:
            # Upstash format: use rediss:// for SSL and token auth
            if redis_url.startswith("https://"):
                redis_url = redis_url.replace("https://", "rediss://")
            self.redis_url = redis_url
            self.redis_token = redis_token
            self.is_upstash = True
            logger.info("Using Upstash Redis for queue management")
        else:
            self.redis_url = redis_url
            self.redis_token = None
            self.is_upstash = False

        self.redis: Optional[redis.Redis] = None
        self.queues: Dict[str, Dict] = {}
        self.processors: Dict[str, Callable] = {}
        self.active_workers: Dict[str, bool] = {}
        
        # Optimized batch processing settings
        self.batch_size = 20  # Increased batch size
        self.batch_timeout = 10.0  # Increased timeout for fewer flushes
        self.global_context_batch: List[Dict] = []
        self.last_batch_flush = time.time()
        self.batch_retry_count = 0
        self.max_batch_retries = 3
        
        # Enhanced cache for frequent data
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 120  # Increased TTL to 2 minutes
        self.cache_last_cleanup = time.time()
        self.hot_keys = set()  # Track frequently accessed keys
        
        # Real-time subscribers
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # Performance metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "avg_processing_time": 0.0,
            "active_queues": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "redis_timeouts": 0,
            "batch_retries": 0
        }
        
    async def connect(self):
        """Connect to Redis with optimized settings for Upstash"""
        try:
            if USING_UPSTASH:
                # Use Upstash Redis library directly
                if self.redis_url.startswith("https://") and self.redis_token:
                    # Create Upstash Redis client from URL and token
                    self.redis = AsyncRedis(url=self.redis_url, token=self.redis_token)
                else:
                    # Create from environment variables if available
                    self.redis = AsyncRedis.from_env()
                
                # Set flag for Upstash
                self.is_upstash = True
                logger.info("Using Upstash Redis native client")
            else:
                # Fallback to standard Redis
                if self.redis_token:
                    # Upstash Redis with token authentication
                    self.redis = redis.Redis(
                        host=self.redis_url.replace("rediss://", "").replace("redis://", ""),
                        port=6379,
                        password=self.redis_token,
                        ssl=True,
                        decode_responses=True,
                        socket_timeout=10.0,
                        socket_connect_timeout=8.0,
                        socket_keepalive=True,
                        health_check_interval=120,
                        retry_on_timeout=True,
                        retry=3
                    )
                else:
                    # Standard Redis connection
                    self.redis = redis.from_url(
                        self.redis_url, 
                        decode_responses=True,
                        health_check_interval=30
                    )
            
            # Test connection
            await self.redis.ping()
            logger.info("✅ Connected to Redis queue system")
            
            # Start background tasks
            asyncio.create_task(self._batch_processor())
            asyncio.create_task(self._metrics_collector())
            asyncio.create_task(self._cache_cleanup())
            
        except ImportError as ie:
            logger.error(f"❌ Redis import error: {ie}. Install with 'pip install upstash-redis'")
            self.redis = None  # Set to None to allow fallback to local cache
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None  # Set to None to allow fallback to local cache
    
    async def create_queue(self, queue_name: str, config: Dict[str, Any] = None) -> bool:
        """Create a new queue with configuration and handle Redis unavailability"""
        try:
            default_config = {
                "max_concurrency": 5,
                "retry_delay": 1000,  # ms
                "max_retries": 3,
                "dead_letter_queue": f"{queue_name}_dlq"
            }
            
            if config:
                default_config.update(config)
            
            self.queues[queue_name] = default_config
            
            # Initialize Redis structures if Redis is available
            if self.redis:
                try:
                    # Use pipeline for efficiency
                    pipeline = self.redis.pipeline()
                    pipeline.delete(f"queue:{queue_name}")
                    pipeline.delete(f"queue:{queue_name}:processing")
                    pipeline.delete(f"queue:{queue_name}:completed")
                    pipeline.delete(f"queue:{queue_name}:failed")
                    
                    # Execute with timeout
                    await asyncio.wait_for(pipeline.execute(), timeout=5.0)
                    logger.info(f"📦 Created queue: {queue_name} with Redis structures")
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Failed to initialize Redis structures for queue {queue_name}: {e}")
                    logger.info(f"📦 Created queue: {queue_name} in memory only")
            else:
                logger.info(f"📦 Created queue: {queue_name} in memory only (Redis unavailable)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
            return False
    
    async def add_task(self, queue_name: str, task_type: str, payload: Dict[str, Any], 
                      priority: TaskPriority = TaskPriority.NORMAL, 
                      delay_ms: int = 0, agent_id: str = None,
                      correlation_id: str = None) -> str:
        """Add task to queue with enhanced features"""
        
        task_id = str(uuid.uuid4())
        task = QueueTask(
            id=task_id,
            queue_name=queue_name,
            task_type=task_type,
            payload=payload,
            priority=priority,
            delay_ms=delay_ms,
            agent_id=agent_id,
            correlation_id=correlation_id
        )
        
        try:
            # Store task data
            await self.redis.hset(
                f"task:{task_id}", 
                mapping={
                    "data": json.dumps(asdict(task), default=str),
                    "queue": queue_name,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat()
                }
            )
            
            # Add to appropriate queue based on delay
            if delay_ms > 0:
                score = time.time() * 1000 + delay_ms
                await self.redis.zadd(f"queue:{queue_name}:delayed", {task_id: score})
            else:
                # Use priority for scoring
                score = priority.value
                await self.redis.zadd(f"queue:{queue_name}", {task_id: score})
            
            # Publish real-time event
            await self._publish_event("task_added", {
                "task_id": task_id,
                "queue": queue_name,
                "type": task_type,
                "agent_id": agent_id,
                "priority": priority.value
            })
            
            logger.info(f"➕ Added task {task_id} to queue {queue_name}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to add task to queue {queue_name}: {e}")
            raise
    
    async def process_queue(self, queue_name: str, processor: Callable):
        """Start processing tasks from a queue"""
        if queue_name not in self.queues:
            raise ValueError(f"Queue {queue_name} does not exist")
        
        self.processors[queue_name] = processor
        self.active_workers[queue_name] = True
        
        logger.info(f"🔄 Started processing queue: {queue_name}")
        
        # Start worker
        asyncio.create_task(self._worker(queue_name))
    
    async def _worker(self, queue_name: str):
        """Worker function to process tasks from queue"""
        config = self.queues[queue_name]
        processor = self.processors[queue_name]
        
        while self.active_workers.get(queue_name, False):
            try:
                # Check if Redis is available
                if not self.redis:
                    logger.warning(f"Redis not available for queue {queue_name}, waiting...")
                    await asyncio.sleep(5)  # Wait longer when Redis is unavailable
                    continue
                    
                # Move delayed tasks to main queue
                await self._process_delayed_tasks(queue_name)
                
                # Get next task with priority
                try:
                    task_id = await asyncio.wait_for(
                        self.redis.zpopmax(f"queue:{queue_name}"),
                        timeout=3.0
                    )
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.5)
                    continue
                except Exception as e:
                    logger.error(f"Error getting task from queue {queue_name}: {e}")
                    await asyncio.sleep(1)
                    continue
                
                if not task_id:
                    await asyncio.sleep(0.1)
                    continue
                
                # Extract task ID based on Upstash or standard Redis response format
                if isinstance(task_id, list) and len(task_id) > 0:
                    task_id = task_id[0][0]  # Standard Redis format
                elif isinstance(task_id, tuple) and len(task_id) > 0:
                    task_id = task_id[0]  # Possible alternative format
                elif isinstance(task_id, dict) and 'member' in task_id:
                    task_id = task_id['member']  # Upstash format
                else:
                    logger.warning(f"Unexpected task_id format: {task_id}")
                    await asyncio.sleep(0.1)
                    continue
                
                # Get task data
                try:
                    task_data = await asyncio.wait_for(
                        self.redis.hget(f"task:{task_id}", "data"),
                        timeout=3.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    logger.error(f"Error getting task data: {e}")
                    await asyncio.sleep(0.5)
                    continue
                    
                if not task_data:
                    continue
                
                task_dict = json.loads(task_data)
                task = QueueTask(**task_dict)
                
                # Update task status
                task.status = TaskStatus.PROCESSING
                task.updated_at = datetime.now()
                
                await self._update_task(task)
                
                # Move to processing set
                try:
                    await asyncio.wait_for(
                        self.redis.sadd(f"queue:{queue_name}:processing", task_id),
                        timeout=3.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Error adding task to processing set: {e}")
                
                # Publish processing event
                await self._publish_event("task_processing", {
                    "task_id": task_id,
                    "queue": queue_name,
                    "agent_id": task.agent_id
                })
                
                # Process task
                start_time = time.time()
                try:
                    result = await processor(task)
                    
                    # Task completed successfully
                    task.status = TaskStatus.COMPLETED
                    processing_time = time.time() - start_time
                    
                    await self._complete_task(task, result, processing_time)
                    
                except Exception as e:
                    # Task failed
                    task.status = TaskStatus.FAILED
                    processing_time = time.time() - start_time
                    
                    await self._handle_task_failure(task, str(e), processing_time)
                
                # Remove from processing set
                try:
                    await asyncio.wait_for(
                        self.redis.srem(f"queue:{queue_name}:processing", task_id),
                        timeout=3.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Error removing task from processing set: {e}")
                
            except Exception as e:
                logger.error(f"Worker error in queue {queue_name}: {e}")
                await asyncio.sleep(1)
    
    async def _process_delayed_tasks(self, queue_name: str):
        """Move ready delayed tasks to main queue with error handling"""
        # Skip if Redis is not available
        if not self.redis:
            return
            
        try:
            current_time = time.time() * 1000
            
            # Get ready tasks with timeout protection
            try:
                ready_tasks = await asyncio.wait_for(
                    self.redis.zrangebyscore(
                        f"queue:{queue_name}:delayed", 
                        0, current_time, 
                        withscores=True
                    ),
                    timeout=3.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Error getting delayed tasks: {e}")
                return
            
            # Process each ready task
            for task_id, score in ready_tasks:
                try:
                    # Move to main queue
                    await asyncio.wait_for(
                        self.redis.zrem(f"queue:{queue_name}:delayed", task_id),
                        timeout=2.0
                    )
                    
                    # Get task priority
                    task_data = await asyncio.wait_for(
                        self.redis.hget(f"task:{task_id}", "data"),
                        timeout=2.0
                    )
                    
                    if task_data:
                        task_dict = json.loads(task_data)
                        priority = task_dict.get("priority", TaskPriority.NORMAL.value)
                        await asyncio.wait_for(
                            self.redis.zadd(f"queue:{queue_name}", {task_id: priority}),
                            timeout=2.0
                        )
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Error processing delayed task {task_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error in _process_delayed_tasks: {e}")
    
    async def _complete_task(self, task: QueueTask, result: Any, processing_time: float):
        """Handle task completion with enhanced event data"""
        task.updated_at = datetime.now()
        
        # Update task with result
        await self.redis.hset(f"task:{task.id}", mapping={
            "data": json.dumps(asdict(task), default=str),
            "result": json.dumps(result, default=str) if result else "",
            "processing_time": processing_time,
            "status": task.status.value
        })
        
        # Move to completed set
        await self.redis.sadd(f"queue:{task.queue_name}:completed", task.id)
        
        # Update metrics
        self.metrics["tasks_processed"] += 1
        self._update_avg_processing_time(processing_time)
        
        # Batch context update if it's an agent result
        if task.agent_id and result:
            await self._add_to_context_batch(task.agent_id, result)
        
        # Publish enhanced completion event
        await self._publish_event("task_completed", {
            "task_id": task.id,
            "task_type": task.task_type,
            "queue": task.queue_name,
            "agent_id": task.agent_id,
            "session_id": task.payload.get("session_id"),
            "processing_time": processing_time,
            "result_size": len(str(result)) if result else 0,
            "confidence": result.get("confidence") if isinstance(result, dict) else None,
            "correlation_id": task.correlation_id
        })
        
        logger.info(f"✅ Task {task.id} ({task.agent_id}) completed in {processing_time:.2f}s")
    
    async def _handle_task_failure(self, task: QueueTask, error: str, processing_time: float):
        """Handle task failure and retry logic"""
        task.retry_count += 1
        task.updated_at = datetime.now()
        
        if task.retry_count <= task.max_retries:
            # Retry task
            task.status = TaskStatus.RETRYING
            delay_ms = task.retry_count * self.queues[task.queue_name].get("retry_delay", 1000)
            
            # Add back to delayed queue
            score = time.time() * 1000 + delay_ms
            await self.redis.zadd(f"queue:{task.queue_name}:delayed", {task.id: score})
            
            logger.warning(f"🔄 Retrying task {task.id} (attempt {task.retry_count})")
            
        else:
            # Move to dead letter queue
            dlq_name = self.queues[task.queue_name].get("dead_letter_queue")
            if dlq_name:
                await self.redis.sadd(f"queue:{dlq_name}", task.id)
            
            # Move to failed set
            await self.redis.sadd(f"queue:{task.queue_name}:failed", task.id)
            
            self.metrics["tasks_failed"] += 1
            
            logger.error(f"❌ Task {task.id} failed permanently: {error}")
        
        # Update task data
        await self.redis.hset(f"task:{task.id}", mapping={
            "data": json.dumps(asdict(task), default=str),
            "error": error,
            "processing_time": processing_time,
            "status": task.status.value
        })
        
        # Publish failure event
        await self._publish_event("task_failed", {
            "task_id": task.id,
            "queue": task.queue_name,
            "agent_id": task.agent_id,
            "error": error,
            "retry_count": task.retry_count,
            "will_retry": task.retry_count <= task.max_retries
        })
    
    async def _add_to_context_batch(self, agent_id: str, result: Any):
        """Add agent result to global context batch"""
        self.global_context_batch.append({
            "agent_id": agent_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Flush batch if it's full or timeout reached
        if (len(self.global_context_batch) >= self.batch_size or 
            time.time() - self.last_batch_flush > self.batch_timeout):
            await self._flush_context_batch()
    
    async def _flush_context_batch(self):
        """Flush global context batch to shared memory with optimized batching"""
        if not self.global_context_batch:
            return
        
        batch_id = str(uuid.uuid4())
        batch = BatchUpdate(
            batch_id=batch_id,
            updates=self.global_context_batch.copy(),
            created_at=datetime.now()
        )
        
        # Compress batch data for Upstash efficiency
        batch_data = json.dumps(asdict(batch), default=str)
        
        try:
            # Use pipeline for better performance with timeout protection
            pipeline = self.redis.pipeline()
            
            # Store batch in Redis
            pipeline.hset(
                f"context_batch:{batch_id}",
                mapping={
                    "data": batch_data,
                    "processed": False,
                    "size": len(self.global_context_batch),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Add to processing queue
            pipeline.lpush("context_batches", batch_id)
            
            # Set TTL for automatic cleanup (24 hours)
            pipeline.expire(f"context_batch:{batch_id}", 86400)
            
            # Execute pipeline with timeout
            await asyncio.wait_for(pipeline.execute(), timeout=5.0)
            
            # Publish batch event
            await self._publish_event("context_batch_created", {
                "batch_id": batch_id,
                "update_count": len(self.global_context_batch)
            })
            
            logger.info(f"📦 Flushed context batch {batch_id} with {len(self.global_context_batch)} updates")
            
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Failed to flush context batch: {e}, will retry on next cycle")
            # Don't clear the batch so it can be retried
            return
        
        # Clear batch only on success
        self.global_context_batch.clear()
        self.last_batch_flush = time.time()
    
    async def _batch_processor(self):
        """Background task to process context batches with improved timeout handling"""
        while True:
            try:
                # Check for batches to process with timeout protection
                try:
                    batch_id = await asyncio.wait_for(
                        self.redis.brpop("context_batches", timeout=1),
                        timeout=5.0  # 5 second timeout
                    )
                except asyncio.TimeoutError:
                    # Just continue the loop if timeout occurs
                    await asyncio.sleep(1)
                    continue
                except Exception as redis_error:
                    logger.error(f"Redis brpop error: {redis_error}")
                    await asyncio.sleep(2)  # Slightly longer sleep on error
                    continue
                
                if batch_id:
                    batch_id = batch_id[1]  # Extract from brpop result
                    
                    # Get batch data with timeout protection
                    try:
                        batch_data = await asyncio.wait_for(
                            self.redis.hget(f"context_batch:{batch_id}", "data"),
                            timeout=5.0
                        )
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.error(f"Failed to get batch data: {e}")
                        continue
                        
                    if batch_data:
                        batch_dict = json.loads(batch_data)
                        batch = BatchUpdate(**batch_dict)
                        
                        # Process batch updates
                        await self._process_context_batch(batch)
                        
                        # Mark as processed - with error handling
                        try:
                            await asyncio.wait_for(
                                self.redis.hset(f"context_batch:{batch_id}", "processed", True),
                                timeout=3.0
                            )
                            
                            # Cache the result for faster access
                            self._cache_set(f"batch:{batch_id}", {"processed": True, "timestamp": time.time()})
                            
                            # Clean up batch data after processing to save memory
                            if self.is_upstash:  # More aggressive cleanup for Upstash
                                await self.redis.expire(f"context_batch:{batch_id}", 300)  # 5 minutes TTL
                        except Exception as update_error:
                            logger.error(f"Failed to update batch status: {update_error}")
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(2)  # Longer sleep on general errors
    
    async def _process_context_batch(self, batch: BatchUpdate):
        """Process a context batch update"""
        # This would integrate with your memory manager
        # For now, just publish the updates
        await self._publish_event("context_batch_processed", {
            "batch_id": batch.batch_id,
            "updates": batch.updates
        })
    
    async def _update_task(self, task: QueueTask):
        """Update task in Redis"""
        await self.redis.hset(
            f"task:{task.id}",
            mapping={
                "data": json.dumps(asdict(task), default=str),
                "status": task.status.value,
                "updated_at": task.updated_at.isoformat()
            }
        )
    
    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        current_avg = self.metrics["avg_processing_time"]
        total_tasks = self.metrics["tasks_processed"]
        
        if total_tasks == 1:
            self.metrics["avg_processing_time"] = processing_time
        else:
            self.metrics["avg_processing_time"] = (
                (current_avg * (total_tasks - 1) + processing_time) / total_tasks
            )
    
    async def _metrics_collector(self):
        """Background task to collect and update metrics"""
        while True:
            try:
                # Update active queues count
                self.metrics["active_queues"] = len([
                    q for q, active in self.active_workers.items() if active
                ])
                
                # Store metrics in Redis
                await self.redis.hset(
                    "queue_metrics",
                    mapping={
                        "data": json.dumps(self.metrics),
                        "updated_at": datetime.now().isoformat()
                    }
                )
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(10)
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish real-time event to subscribers with resilient processing"""
        # Determine if this is a critical event that needs synchronous processing
        is_critical = event_type in ["task_failed", "execution_completed"]
        
        # Use minimal context for all events to reduce payload size
        enriched_data = {
            **data,
            "queue_metrics": {
                "active_queues": len([q for q, active in self.active_workers.items() if active])
            }
        }
        
        # Only add detailed metrics for critical events
        if is_critical:
            enriched_data["queue_metrics"].update({
                "total_tasks_processed": self.metrics["tasks_processed"],
                "avg_processing_time": self.metrics["avg_processing_time"]
            })
        
        event = {
            "type": event_type,
            "data": enriched_data,
            "timestamp": datetime.now().isoformat(),
            "source": "queue_manager"
        }
        
        # Publish to Redis if available
        if self.redis:
            try:
                if is_critical:
                    # Critical events: wait with timeout
                    await asyncio.wait_for(
                        self.redis.publish("agentflow_events", json.dumps(event, default=str)),
                        timeout=2.0  # Reduced timeout
                    )
                    logger.debug(f"📡 Published critical event: {event_type}")
                else:
                    # Non-critical events: fire and forget
                    asyncio.create_task(self._async_publish(event_type, event))
                    logger.debug(f"📡 Queued non-critical event: {event_type}")
            except (asyncio.TimeoutError, Exception) as e:
                # Just log the error but continue with local subscribers
                if is_critical:
                    logger.warning(f"Failed to publish critical event {event_type}: {e}")
                else:
                    logger.debug(f"Failed to publish non-critical event {event_type}: {e}")
        else:
            # Redis not available, log only for critical events
            if is_critical:
                logger.warning(f"Redis unavailable for publishing critical event: {event_type}")
        
        # Always process local subscribers synchronously for reliability
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
    
    async def _async_publish(self, event_type: str, event: Dict):
        """Asynchronous fire-and-forget event publishing with error handling"""
        if not self.redis:
            return  # Skip if Redis is not available
            
        try:
            # Use timeout to prevent blocking
            await asyncio.wait_for(
                self.redis.publish("agentflow_events", json.dumps(event, default=str)),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            # Just log the timeout but don't propagate it
            logger.debug(f"Async publish timeout for {event_type}")
        except Exception as e:
            # Just log the error but don't propagate it
            logger.debug(f"Async publish failed for {event_type}: {e}")
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to real-time events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        if queue_name not in self.queues:
            return {}
        
        try:
            pending = await self.redis.zcard(f"queue:{queue_name}")
            processing = await self.redis.scard(f"queue:{queue_name}:processing")
            completed = await self.redis.scard(f"queue:{queue_name}:completed")
            failed = await self.redis.scard(f"queue:{queue_name}:failed")
            delayed = await self.redis.zcard(f"queue:{queue_name}:delayed")
            
            return {
                "queue_name": queue_name,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "delayed": delayed,
                "total": pending + processing + completed + failed + delayed,
                "active": self.active_workers.get(queue_name, False),
                "config": self.queues[queue_name]
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        # Get Redis memory usage if not Upstash (Upstash doesn't support INFO command)
        redis_info = {}
        if not self.is_upstash:
            try:
                info = await self.redis.info()
                redis_info = {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {e}")
        
        return {
            **self.metrics,
            "active_queues": len([q for q, active in self.active_workers.items() if active]),
            "total_queues": len(self.queues),
            "global_context_batch_size": len(self.global_context_batch),
            "cache_size": len(self.cache),
            "cache_efficiency": self._calculate_cache_efficiency(),
            "redis_info": redis_info,
            "is_upstash": self.is_upstash
        }
    
    def _calculate_cache_efficiency(self) -> float:
        """Calculate cache hit ratio"""
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total == 0:
            return 0.0
        return self.metrics["cache_hits"] / total
    
    async def _cache_cleanup(self):
        """Periodically clean up expired cache entries with batch processing"""
        while True:
            try:
                # Only run cleanup if cache is large enough to warrant it
                if len(self.cache) < 100:
                    await asyncio.sleep(60)  # Less frequent cleanup for small caches
                    continue
                    
                now = time.time()
                expired_keys = []
                hot_keys_to_remove = []
                processed = 0
                batch_size = 100  # Process in batches to avoid blocking
                
                # Find expired entries in batches
                for key, entry in list(self.cache.items())[:batch_size]:
                    processed += 1
                    
                    # Use entry-specific TTL if available
                    ttl = entry.get("ttl", self.cache_ttl)
                    
                    if now - entry.get("timestamp", 0) > ttl:
                        expired_keys.append(key)
                        
                        # Also remove from hot keys if present
                        if key in self.hot_keys:
                            hot_keys_to_remove.append(key)
                
                # Remove expired entries
                for key in expired_keys:
                    del self.cache[key]
                    
                # Clean up hot keys set
                for key in hot_keys_to_remove:
                    self.hot_keys.discard(key)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries (processed {processed}/{len(self.cache)})")
                
                # Adaptive sleep based on cache size
                if len(self.cache) > 1000:
                    await asyncio.sleep(15)  # More frequent cleanup for large caches
                else:
                    await asyncio.sleep(30)  # Normal interval
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)  # Longer sleep on error
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL check and hot key tracking"""
        entry = self.cache.get(key)
        if not entry:
            self.metrics["cache_misses"] += 1
            return None
            
        # Check if expired
        if time.time() - entry.get("timestamp", 0) > self.cache_ttl:
            del self.cache[key]
            self.metrics["cache_misses"] += 1
            return None
        
        # Track frequently accessed keys
        if key not in self.hot_keys and key.startswith(("task_status:", "batch:", "queue:")):
            self.hot_keys.add(key)
            # Extend TTL for hot keys
            entry["ttl"] = self.cache_ttl * 2
            
        self.metrics["cache_hits"] += 1
        return entry.get("value")
    
    def _cache_set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp and adaptive TTL"""
        # Use longer TTL for hot keys
        ttl = self.cache_ttl * 2 if key in self.hot_keys else self.cache_ttl
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }
    
    async def stop_queue(self, queue_name: str):
        """Stop processing a queue"""
        self.active_workers[queue_name] = False
        logger.info(f"🛑 Stopped queue: {queue_name}")
    
    async def stop_all(self):
        """Stop all queue processing"""
        for queue_name in self.active_workers:
            self.active_workers[queue_name] = False
        
        if self.redis:
            await self.redis.close()
        
        logger.info("🛑 Stopped all queue processing")

# Global queue manager instance
queue_manager = EnhancedQueueManager()
