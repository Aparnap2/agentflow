#!/usr/bin/env python3
"""
Simple test script for Redis adapter
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

async def test_redis_adapter():
    """Test the Redis adapter"""
    logger.info("Testing Redis adapter...")
    
    # Import our modules
    try:
        from task_queue.upstash_adapter import UpstashAdapter
        logger.info("Successfully imported UpstashAdapter")
    except Exception as e:
        logger.error(f"Failed to import UpstashAdapter: {e}")
    
    try:
        from task_queue.memory_fallback import InMemoryFallback
        logger.info("Successfully imported InMemoryFallback")
    except Exception as e:
        logger.error(f"Failed to import InMemoryFallback: {e}")
    
    try:
        from task_queue.enhanced_queue_manager import queue_manager
        logger.info("Successfully imported queue_manager")
    except Exception as e:
        logger.error(f"Failed to import queue_manager: {e}")
    
    logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_redis_adapter())