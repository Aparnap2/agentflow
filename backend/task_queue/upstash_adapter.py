"""
Adapter for Upstash Redis to make it compatible with standard Redis client
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from loguru import logger

class UpstashAdapter:
    """Adapter to make Upstash Redis API compatible with standard Redis"""
    
    def __init__(self, client):
        """Initialize with an Upstash Redis client"""
        self.client = client
        self.is_upstash = True
    
    async def ping(self):
        """Test connection"""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Upstash ping error: {e}")
            return False
    
    async def hset(self, key: str, field: str = None, value: Any = None, mapping: Dict[str, Any] = None):
        """Set hash fields to handle both field/value and mapping formats"""
        try:
            if mapping:
                # Handle mapping parameter by setting each field individually
                result = 0
                for field_name, field_value in mapping.items():
                    field_result = await self.client.hset(key, field_name, field_value)
                    result += field_result if isinstance(field_result, int) else 1
                return result
            else:
                # Handle direct field/value
                return await self.client.hset(key, field, value)
        except Exception as e:
            logger.error(f"Upstash hset error: {e}")
            raise
    
    async def hget(self, key: str, field: str):
        """Get hash field"""
        try:
            return await self.client.hget(key, field)
        except Exception as e:
            logger.error(f"Upstash hget error: {e}")
            return None
    
    async def delete(self, *keys):
        """Delete keys (Upstash uses delete)"""
        try:
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Upstash delete error: {e}")
            return 0
    
    async def get(self, key: str):
        """Get a value"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Upstash get error: {e}")
            return None
    
    async def set(self, key: str, value: str):
        """Set a value"""
        try:
            return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Upstash set error: {e}")
            return False
    
    async def setex(self, key: str, seconds: int, value: str):
        """Set with expiration"""
        try:
            return await self.client.setex(key, seconds, value)
        except Exception as e:
            logger.error(f"Upstash setex error: {e}")
            return False
    
    async def zadd(self, key: str, mapping: Dict[str, float]):
        """Add to sorted set with mapping format"""
        try:
            # Upstash expects {score: member} format, but we're given {member: score}
            result = 0
            for member, score in mapping.items():
                # Convert to Upstash format
                upstash_mapping = {score: member}
                add_result = await self.client.zadd(key, upstash_mapping)
                result += add_result if isinstance(add_result, int) else 1
            return result
        except Exception as e:
            logger.error(f"Upstash zadd error: {e}")
            return 0
    
    async def zrangebyscore(self, key: str, min_score: float, max_score: float, withscores=False):
        """Get range from sorted set by score"""
        try:
            result = await self.client.zrangebyscore(key, min_score, max_score)
            
            if not withscores or not result:
                return result
            
            # Add scores for compatibility with standard Redis format
            scores = []
            for member in result:
                try:
                    score = await self.client.zscore(key, member)
                    scores.append((member, score))
                except Exception:
                    # Skip if we can't get the score
                    pass
            
            return scores
        except Exception as e:
            logger.error(f"Upstash zrangebyscore error: {e}")
            return []
    
    async def zpopmax(self, key: str):
        """Pop highest scored member"""
        try:
            result = await self.client.zpopmax(key, 1)
            if not result or len(result) < 2:
                return []
            
            # Format to match standard Redis [(member, score)]
            return [(result[0], result[1])]
        except Exception as e:
            logger.error(f"Upstash zpopmax error: {e}")
            return []
    
    async def zrem(self, key: str, member: str):
        """Remove from sorted set"""
        try:
            return await self.client.zrem(key, member)
        except Exception as e:
            logger.error(f"Upstash zrem error: {e}")
            return 0
    
    async def zcard(self, key: str):
        """Get sorted set cardinality"""
        try:
            return await self.client.zcard(key)
        except Exception as e:
            logger.error(f"Upstash zcard error: {e}")
            return 0
    
    async def sadd(self, key: str, member: str):
        """Add to set"""
        try:
            return await self.client.sadd(key, member)
        except Exception as e:
            logger.error(f"Upstash sadd error: {e}")
            return 0
    
    async def srem(self, key: str, member: str):
        """Remove from set"""
        try:
            return await self.client.srem(key, member)
        except Exception as e:
            logger.error(f"Upstash srem error: {e}")
            return 0
    
    async def scard(self, key: str):
        """Get set cardinality"""
        try:
            return await self.client.scard(key)
        except Exception as e:
            logger.error(f"Upstash scard error: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int):
        """Set key expiration"""
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Upstash expire error: {e}")
            return 0
    
    async def lpush(self, key: str, value: str):
        """Push to list"""
        try:
            return await self.client.lpush(key, value)
        except Exception as e:
            logger.error(f"Upstash lpush error: {e}")
            return 0
    
    async def brpop(self, key: str, timeout: int = 0):
        """Blocking pop from list (Upstash doesn't support this directly)"""
        try:
            # Simulate brpop with rpop and sleep
            result = await self.client.rpop(key)
            if result:
                return [key, result]
            
            # If no result, sleep briefly and return None
            await asyncio.sleep(0.5)
            return None
        except Exception as e:
            logger.error(f"Upstash brpop simulation error: {e}")
            return None
    
    async def publish(self, channel: str, message: str):
        """Publish message to channel"""
        try:
            return await self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Upstash publish error: {e}")
            return 0
    
    async def close(self):
        """Close connection (no-op for Upstash)"""
        pass
    
    def pipeline(self):
        """Create a pipeline"""
        return UpstashPipeline(self.client)

class UpstashPipeline:
    """Pipeline implementation for Upstash Redis"""
    
    def __init__(self, client):
        """Initialize with Upstash client"""
        self.client = client
        self.commands = []
    
    def hset(self, key: str, mapping: Dict[str, Any] = None, **kwargs):
        """Add hset command to pipeline"""
        if mapping:
            for field, value in mapping.items():
                self.commands.append(("hset", key, field, value))
        else:
            field = kwargs.get("field", list(kwargs.keys())[0])
            value = kwargs.get("value", kwargs[field])
            self.commands.append(("hset", key, field, value))
        return self
    
    def delete(self, key: str):
        """Add delete command to pipeline"""
        self.commands.append(("delete", key))
        return self
    
    def setex(self, key: str, seconds: int, value: str):
        """Add setex command to pipeline"""
        self.commands.append(("setex", key, seconds, value))
        return self
    
    def lpush(self, key: str, value: str):
        """Add lpush command to pipeline"""
        self.commands.append(("lpush", key, value))
        return self
    
    def expire(self, key: str, seconds: int):
        """Add expire command to pipeline"""
        self.commands.append(("expire", key, seconds))
        return self
    
    async def execute(self):
        """Execute pipeline commands"""
        results = []
        for cmd in self.commands:
            try:
                if cmd[0] == "hset":
                    results.append(await self.client.hset(cmd[1], cmd[2], cmd[3]))
                elif cmd[0] == "delete":
                    results.append(await self.client.delete(cmd[1]))
                elif cmd[0] == "setex":
                    results.append(await self.client.setex(cmd[1], cmd[2], cmd[3]))
                elif cmd[0] == "lpush":
                    results.append(await self.client.lpush(cmd[1], cmd[2]))
                elif cmd[0] == "expire":
                    results.append(await self.client.expire(cmd[1], cmd[2]))
            except Exception as e:
                logger.error(f"Upstash pipeline error executing {cmd[0]}: {e}")
                results.append(None)
        
        self.commands = []  # Clear commands after execution
        return results