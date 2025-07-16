"""
In-memory fallback for Redis operations when Redis is unavailable
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from loguru import logger

class InMemoryFallback:
    """In-memory implementation of Redis-like operations for fallback"""
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.hash_data = {}  # For hset/hget
        self.sorted_sets = {}  # For zadd/zrem/etc
        self.sets = {}  # For sadd/srem/etc
        self.lists = {}  # For lpush/brpop/etc
        self.key_values = {}  # For simple key-value
        self.expiry = {}  # For key expiration
        self.pubsub = {}  # For publish/subscribe
        self.is_upstash = False
    
    async def ping(self):
        """Test connection (always succeeds)"""
        return True
    
    async def hset(self, key: str, field: str = None, value: Any = None, mapping: Dict[str, Any] = None):
        """Set hash fields"""
        if key not in self.hash_data:
            self.hash_data[key] = {}
        
        if mapping:
            for field_name, field_value in mapping.items():
                self.hash_data[key][field_name] = field_value
            return len(mapping)
        else:
            self.hash_data[key][field] = value
            return 1
    
    async def hget(self, key: str, field: str):
        """Get hash field"""
        if key not in self.hash_data or field not in self.hash_data[key]:
            return None
        return self.hash_data[key][field]
    
    async def delete(self, *keys):
        """Delete keys"""
        count = 0
        for key in keys:
            # Check all data structures
            for data_dict in [self.hash_data, self.sorted_sets, self.sets, self.lists, self.key_values]:
                if key in data_dict:
                    del data_dict[key]
                    count += 1
        return count
    
    async def get(self, key: str):
        """Get a value"""
        return self.key_values.get(key)
    
    async def set(self, key: str, value: str):
        """Set a value"""
        self.key_values[key] = value
        return True
    
    async def setex(self, key: str, seconds: int, value: str):
        """Set with expiration"""
        self.key_values[key] = value
        self.expiry[key] = time.time() + seconds
        return True
    
    async def zadd(self, key: str, mapping: Dict[str, float]):
        """Add to sorted set"""
        if key not in self.sorted_sets:
            self.sorted_sets[key] = {}
        
        for member, score in mapping.items():
            self.sorted_sets[key][member] = score
        
        return len(mapping)
    
    async def zrangebyscore(self, key: str, min_score: float, max_score: float, withscores=False):
        """Get range from sorted set by score"""
        if key not in self.sorted_sets:
            return []
        
        # Filter by score and sort
        items = [(member, score) for member, score in self.sorted_sets[key].items() 
                if min_score <= score <= max_score]
        items.sort(key=lambda x: x[1])
        
        if withscores:
            return items
        else:
            return [item[0] for item in items]
    
    async def zpopmax(self, key: str):
        """Pop highest scored member"""
        if key not in self.sorted_sets or not self.sorted_sets[key]:
            return []
        
        # Find max score item
        max_item = max(self.sorted_sets[key].items(), key=lambda x: x[1])
        member, score = max_item
        
        # Remove from set
        del self.sorted_sets[key][member]
        
        return [(member, score)]
    
    async def zrem(self, key: str, member: str):
        """Remove from sorted set"""
        if key not in self.sorted_sets or member not in self.sorted_sets[key]:
            return 0
        
        del self.sorted_sets[key][member]
        return 1
    
    async def zcard(self, key: str):
        """Get sorted set cardinality"""
        if key not in self.sorted_sets:
            return 0
        return len(self.sorted_sets[key])
    
    async def sadd(self, key: str, member: str):
        """Add to set"""
        if key not in self.sets:
            self.sets[key] = set()
        
        if member in self.sets[key]:
            return 0
        
        self.sets[key].add(member)
        return 1
    
    async def srem(self, key: str, member: str):
        """Remove from set"""
        if key not in self.sets or member not in self.sets[key]:
            return 0
        
        self.sets[key].remove(member)
        return 1
    
    async def scard(self, key: str):
        """Get set cardinality"""
        if key not in self.sets:
            return 0
        return len(self.sets[key])
    
    async def expire(self, key: str, seconds: int):
        """Set key expiration"""
        self.expiry[key] = time.time() + seconds
        return 1
    
    async def lpush(self, key: str, value: str):
        """Push to list"""
        if key not in self.lists:
            self.lists[key] = []
        
        self.lists[key].insert(0, value)  # Insert at beginning
        return len(self.lists[key])
    
    async def brpop(self, key: str, timeout: int = 0):
        """Blocking pop from list"""
        if key not in self.lists or not self.lists[key]:
            return None
        
        value = self.lists[key].pop()  # Remove from end
        return [key, value]
    
    async def publish(self, channel: str, message: str):
        """Publish message to channel"""
        if channel not in self.pubsub:
            return 0
        
        # Store message for subscribers
        for callback in self.pubsub.get(channel, []):
            asyncio.create_task(callback(channel, message))
        
        return len(self.pubsub.get(channel, []))
    
    async def close(self):
        """Close connection (no-op)"""
        pass
    
    def pipeline(self):
        """Create a pipeline"""
        return InMemoryPipeline(self)

class InMemoryPipeline:
    """Pipeline implementation for in-memory fallback"""
    
    def __init__(self, fallback):
        """Initialize with fallback instance"""
        self.fallback = fallback
        self.commands = []
    
    def hset(self, key: str, mapping: Dict[str, Any] = None, **kwargs):
        """Add hset command to pipeline"""
        if mapping:
            self.commands.append(("hset_mapping", key, mapping))
        else:
            field = kwargs.get("field", list(kwargs.keys())[0])
            value = kwargs.get("value", kwargs[field])
            self.commands.append(("hset", key, field, value))
        return self
    
    def delete(self, key: str):
        """Add delete command to pipeline"""
        self.commands.append(("delete", key))
        return self
    
    def lpush(self, key: str, value: str):
        """Add lpush command to pipeline"""
        self.commands.append(("lpush", key, value))
        return self
    
    def expire(self, key: str, seconds: int):
        """Add expire command to pipeline"""
        self.commands.append(("expire", key, seconds))
        return self
    
    def setex(self, key: str, seconds: int, value: str):
        """Add setex command to pipeline"""
        self.commands.append(("setex", key, seconds, value))
        return self
    
    async def execute(self):
        """Execute pipeline commands"""
        results = []
        for cmd in self.commands:
            try:
                if cmd[0] == "hset":
                    results.append(await self.fallback.hset(cmd[1], field=cmd[2], value=cmd[3]))
                elif cmd[0] == "hset_mapping":
                    results.append(await self.fallback.hset(cmd[1], mapping=cmd[2]))
                elif cmd[0] == "delete":
                    results.append(await self.fallback.delete(cmd[1]))
                elif cmd[0] == "lpush":
                    results.append(await self.fallback.lpush(cmd[1], cmd[2]))
                elif cmd[0] == "expire":
                    results.append(await self.fallback.expire(cmd[1], cmd[2]))
                elif cmd[0] == "setex":
                    results.append(await self.fallback.setex(cmd[1], cmd[2], cmd[3]))
            except Exception as e:
                logger.error(f"In-memory pipeline error executing {cmd[0]}: {e}")
                results.append(None)
        
        self.commands = []  # Clear commands after execution
        return results