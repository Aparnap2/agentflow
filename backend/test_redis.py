#!/usr/bin/env python3
\"\"\"
Test script for Redis connection
\"\"\"
import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our queue manager
from task_queue.enhanced_queue_manager import queue_manager

async def test_redis_connection():
    """Test Redis connection and basic operations"""
    logger.info("Testing Redis connection...")
    
    # Connect to Redis
    await queue_manager.connect()
    
    # Create a test queue
    await queue_manager.create_queue("test_queue")
    
    # Add a test task
    task_id = await queue_manager.add_task(
        queue_name="test_queue",
        task_type="test",
        payload={"message": "Hello, Redis!"}
    )
    
    logger.info(f"Added test task: {task_id}")
    
    # Get queue stats
    stats = await queue_manager.get_queue_stats("test_queue")
    logger.info(f"Queue stats: {stats}")
    
    # Get system metrics
    metrics = await queue_manager.get_system_metrics()
    logger.info(f"System metrics: {metrics}")
    
    # Stop all queues
    await queue_manager.stop_all()
    
    logger.info("Redis test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())