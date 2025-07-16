"""
Simple Cache Event System - Integrates with existing queue manager
Triggers cache invalidation and DB access only when needed
"""

import asyncio
from typing import Dict, Any, Set
from loguru import logger
from task_queue.enhanced_queue_manager import queue_manager

class SimpleCacheEvents:
    """Simple event system for cache management"""
    
    def __init__(self):
        self.event_handlers = {}
        self.pending_invalidations: Set[str] = set()
        
    async def trigger_update_event(self, agent_name: str, memory_type: str, is_shared: bool = False):
        """Trigger cache update event"""
        try:
            # Add to pending invalidations
            if is_shared:
                self.pending_invalidations.add("shared_context")
                self.pending_invalidations.add(f"agent_context:{agent_name}")
            else:
                self.pending_invalidations.add(f"agent_memory:{agent_name}")
            
            # Publish event if Redis is available
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                event_data = {
                    "type": "cache_update",
                    "agent_name": agent_name,
                    "memory_type": memory_type,
                    "is_shared": is_shared,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                # Fire-and-forget publish
                asyncio.create_task(self._publish_event("cache_events", event_data))
                
        except Exception as e:
            logger.debug(f"Cache event trigger failed: {e}")
    
    async def trigger_new_upload_event(self, content_type: str, agent_name: str):
        """Trigger new upload event"""
        try:
            # Mark for cache invalidation
            self.pending_invalidations.add(f"search_*")
            self.pending_invalidations.add("shared_context")
            
            # Publish event
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                event_data = {
                    "type": "new_upload",
                    "content_type": content_type,
                    "agent_name": agent_name,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                asyncio.create_task(self._publish_event("cache_events", event_data))
                
        except Exception as e:
            logger.debug(f"New upload event failed: {e}")
    
    async def should_access_db(self, key: str) -> bool:
        """Check if DB access is needed based on pending events"""
        # Check if this key type has pending invalidations
        for pattern in self.pending_invalidations:
            if self._key_matches_pattern(key, pattern):
                return True
        
        # Check for time-based refresh (every 5 minutes for shared context)
        if key.startswith("shared_context"):
            try:
                if hasattr(queue_manager, 'redis') and queue_manager.redis:
                    last_update = await queue_manager.redis.get(f"last_update:{key}")
                    if last_update:
                        import time
                        if time.time() - float(last_update) > 300:  # 5 minutes
                            return True
            except Exception:
                pass
        
        return False
    
    async def mark_db_accessed(self, key: str):
        """Mark that DB was accessed for this key"""
        try:
            # Remove from pending invalidations
            patterns_to_remove = []
            for pattern in self.pending_invalidations:
                if self._key_matches_pattern(key, pattern):
                    patterns_to_remove.append(pattern)
            
            for pattern in patterns_to_remove:
                self.pending_invalidations.discard(pattern)
            
            # Update last access time
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                import time
                await queue_manager.redis.setex(f"last_update:{key}", 3600, str(time.time()))
                
        except Exception as e:
            logger.debug(f"Mark DB accessed failed for {key}: {e}")
    
    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching"""
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return key.startswith(prefix)
        return key == pattern
    
    async def _publish_event(self, channel: str, data: Dict[str, Any]):
        """Publish event to Redis channel"""
        try:
            import json
            await queue_manager.redis.publish(channel, json.dumps(data, default=str))
        except Exception as e:
            logger.debug(f"Event publish failed: {e}")
    
    async def cleanup_pending_events(self):
        """Clean up old pending events"""
        # Keep only recent events (last 100)
        if len(self.pending_invalidations) > 100:
            # Convert to list, keep last 50
            recent_events = list(self.pending_invalidations)[-50:]
            self.pending_invalidations = set(recent_events)

# Global instance
cache_events = SimpleCacheEvents()