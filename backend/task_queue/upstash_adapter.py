"""
Adapter for Upstash Redis to make it compatible with standard Redis client
With added compression and chunking for large payloads to stay under Upstash limits
"""
import asyncio
import json
import zlib
import base64
import time
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
        """Get a value with automatic decompression and chunk reassembly if needed"""
        try:
            value = await self.client.get(key)
            
            # If no value, return None
            if not value:
                return None
                
            # Check if value is chunked
            if isinstance(value, str) and value.startswith("__chunked__:"):
                try:
                    # Extract number of chunks
                    num_chunks = int(value.split(":", 1)[1])
                    
                    # Get metadata
                    metadata_key = f"{key}:chunked_metadata"
                    metadata_json = await self.client.get(metadata_key)
                    
                    if not metadata_json:
                        logger.error(f"Missing chunk metadata for key {key}")
                        return None
                        
                    metadata = json.loads(metadata_json)
                    
                    # Retrieve all chunks
                    chunks = []
                    for i in range(num_chunks):
                        chunk_key = f"{key}:chunk:{i}"
                        chunk = await self.client.get(chunk_key)
                        if not chunk:
                            logger.error(f"Missing chunk {i} for key {key}")
                            return None
                        chunks.append(chunk)
                    
                    # Reassemble the chunks
                    encoded_data = "".join(chunks)
                    
                    # Decode and decompress
                    compressed = base64.b64decode(encoded_data)
                    decompressed = zlib.decompress(compressed)
                    return decompressed.decode('utf-8')
                    
                except Exception as chunk_error:
                    logger.error(f"Error reassembling chunks for key {key}: {chunk_error}")
                    return None
            
            # Check if value is compressed and decompress if needed
            elif isinstance(value, str) and value.startswith("__compressed__:"):
                return self._decompress_value(value)
                
            return value
        except Exception as e:
            logger.error(f"Upstash get error: {e}")
            return None
            
    def _decompress_value(self, value: str) -> str:
        """Decompress a value that was previously compressed"""
        try:
            # Remove the prefix
            if not value.startswith("__compressed__:"):
                return value
                
            encoded = value[len("__compressed__:"):]
            
            # Decode base64, decompress, and convert back to string
            compressed = base64.b64decode(encoded)
            decompressed = zlib.decompress(compressed)
            return decompressed.decode('utf-8')
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return value  # Return original value if decompression fails
    
    async def set(self, key: str, value: str):
        """Set a value"""
        try:
            return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Upstash set error: {e}")
            return False
    
    async def setex(self, key: str, seconds: int, value: str):
        """Set with expiration and automatic compression/chunking for large values"""
        try:
            # Get the size of the value
            value_size = len(value) if isinstance(value, str) else len(json.dumps(value, default=str))
            
            # Upstash limit is 10MB
            UPSTASH_LIMIT = 10_000_000
            
            # If value is extremely large (over 8MB), use chunking
            if value_size > 8_000_000:
                logger.warning(f"Value for key {key} is extremely large: {value_size/1_000_000:.2f}MB - using chunking")
                return await self._store_chunked(key, seconds, value)
            
            # For medium-large values (over 500KB), use compression
            elif value_size > 500_000:
                # Compress the value
                compressed = self._compress_value(value)
                compressed_size = len(compressed)
                
                # Log compression ratio
                logger.info(f"Compressed value for key {key}: {value_size/1_000_000:.2f}MB → {compressed_size/1_000_000:.2f}MB (ratio: {value_size/compressed_size:.1f}x)")
                
                # If still too large after compression, use chunking
                if compressed_size > UPSTASH_LIMIT:
                    logger.warning(f"Compressed value still too large ({compressed_size/1_000_000:.2f}MB) - using chunking")
                    return await self._store_chunked(key, seconds, value)
                
                return await self.client.setex(key, seconds, compressed)
            else:
                # For smaller values, store directly
                return await self.client.setex(key, seconds, value)
        except Exception as e:
            logger.error(f"Upstash setex error: {e}")
            return False
    
    async def _store_chunked(self, key: str, seconds: int, value: str):
        """Store large values by splitting into chunks"""
        try:
            # Convert to string if not already
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            # Compress the value first
            compressed = self._compress_value(value)
            
            # Calculate optimal chunk size (max 5MB per chunk)
            MAX_CHUNK_SIZE = 5_000_000
            
            # Convert to bytes for chunking
            if compressed.startswith("__compressed__:"):
                # Already compressed, extract the base64 part
                encoded_data = compressed[len("__compressed__:"):]
                # No need to decode and re-encode
            else:
                # Compress if not already compressed
                value_bytes = value.encode('utf-8')
                compressed_bytes = zlib.compress(value_bytes, level=9)
                encoded_data = base64.b64encode(compressed_bytes).decode('ascii')
            
            # Split into chunks
            total_length = len(encoded_data)
            num_chunks = (total_length + MAX_CHUNK_SIZE - 1) // MAX_CHUNK_SIZE  # Ceiling division
            
            # Store metadata
            metadata = {
                "total_chunks": num_chunks,
                "total_size": total_length,
                "is_chunked": True,
                "created_at": time.time()
            }
            
            # Store metadata
            await self.client.setex(f"{key}:chunked_metadata", seconds, json.dumps(metadata))
            
            # Store each chunk
            for i in range(num_chunks):
                start_idx = i * MAX_CHUNK_SIZE
                end_idx = min((i + 1) * MAX_CHUNK_SIZE, total_length)
                chunk = encoded_data[start_idx:end_idx]
                
                # Store chunk with same expiration
                chunk_key = f"{key}:chunk:{i}"
                await self.client.setex(chunk_key, seconds, chunk)
            
            logger.info(f"Stored large value for key {key} in {num_chunks} chunks")
            
            # Store a marker in the original key
            return await self.client.setex(key, seconds, f"__chunked__:{num_chunks}")
            
        except Exception as e:
            logger.error(f"Chunking error for key {key}: {e}")
            return False
            
    def _compress_value(self, value: str) -> str:
        """Compress a string value and encode it for storage"""
        try:
            # Convert to string if not already
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            # Convert string to bytes, compress it, and encode as base64
            value_bytes = value.encode('utf-8')
            compressed = zlib.compress(value_bytes, level=9)  # Maximum compression
            encoded = base64.b64encode(compressed).decode('ascii')
            
            # Add a prefix to identify compressed values
            return f"__compressed__:{encoded}"
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return value  # Return original value if compression fails
    
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