"""
State Manager for persisting conversation state
"""

import json
import redis
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

class StateManager:
    """Manages persistent state for agents and conversations"""
    
    def __init__(self):
        """Initialize Redis connection for state persistence"""
        # Handle Upstash Redis URL format
        UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "redis://localhost:6379")
        UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        # Check for Upstash REST URL (implying Upstash Redis) or token and URL
        upstash_rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
        if upstash_rest_url or (UPSTASH_REDIS_REST_TOKEN and "upstash.io" in UPSTASH_REDIS_REST_URL):
            self.UPSTASH_REDIS_REST_URL = UPSTASH_REDIS_REST_URL.replace("https://", "rediss://") if "upstash.io" in UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_URL.startswith("https://") else UPSTASH_REDIS_REST_URL
            self.UPSTASH_REDIS_REST_TOKEN = UPSTASH_REDIS_REST_TOKEN
            logger.info("Using Upstash Redis for state management")
        else:
            self.UPSTASH_REDIS_REST_URL = UPSTASH_REDIS_REST_URL
            self.UPSTASH_REDIS_REST_TOKEN = None
            
        self.redis = None
        self._connect()
        
    def _connect(self):
        """Connect to Redis database"""
        try:
            if self.UPSTASH_REDIS_REST_TOKEN and "upstash.io" in self.UPSTASH_REDIS_REST_URL:
                # Upstash Redis with token authentication
                self.redis = redis.Redis(
                    host=self.UPSTASH_REDIS_REST_URL.replace("rediss://", "").replace("redis://", ""),
                    port=6379,
                    password=self.UPSTASH_REDIS_REST_TOKEN,
                    ssl=True,
                    decode_responses=True
                )
            else:
                # Standard Redis connection
                self.redis = redis.from_url(self.UPSTASH_REDIS_REST_URL, decode_responses=True)
            
            # Test the connection
            self.redis.ping()
            logger.info("Connected to Redis state database")
        except Exception as e:
            logger.warning(f"Redis connection failed, using fallback: {e}")
            self.redis = None
            
    async def persist_conversation(self, conversation_id: str, state: Dict[str, Any]) -> bool:
        """Persist conversation state to Redis"""
        if not self.redis:
            logger.warning("Redis unavailable, using fallback for conversation persistence")
            return self._fallback_persist(conversation_id, state)
            
        try:
            # Convert state to JSON string
            state_json = json.dumps(state)
            
            # Set in Redis with 24-hour expiration
            self.redis.setex(
                f"conversation:{conversation_id}", 
                86400, # 24 hours in seconds
                state_json
            )
            
            logger.info(f"Persisted state for conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist conversation state: {e}")
            return False
            
    async def retrieve_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation state from Redis"""
        if not self.redis:
            logger.warning("Redis unavailable, using fallback for conversation retrieval")
            return self._fallback_retrieve(conversation_id)
            
        try:
            # Get from Redis
            state_json = self.redis.get(f"conversation:{conversation_id}")
            
            if not state_json:
                logger.warning(f"No state found for conversation {conversation_id}")
                return None
                
            # Parse JSON string back to dict
            state = json.loads(state_json)
            
            logger.info(f"Retrieved state for conversation {conversation_id}")
            return state
        except Exception as e:
            logger.error(f"Failed to retrieve conversation state: {e}")
            return None
            
    async def persist_agent_state(self, agent_name: str, state_key: str, state_data: Dict[str, Any]) -> bool:
        """Persist agent-specific state to Redis"""
        if not self.redis:
            return False
            
        try:
            # Convert state to JSON string
            state_json = json.dumps(state_data)
            
            # Set in Redis with 7-day expiration
            self.redis.setex(
                f"agent:{agent_name}:{state_key}", 
                604800, # 7 days in seconds
                state_json
            )
            
            logger.info(f"Persisted {state_key} state for agent {agent_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist agent state: {e}")
            return False
            
    async def retrieve_agent_state(self, agent_name: str, state_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent-specific state from Redis"""
        if not self.redis:
            return None
            
        try:
            # Get from Redis
            state_json = self.redis.get(f"agent:{agent_name}:{state_key}")
            
            if not state_json:
                logger.info(f"No {state_key} state found for agent {agent_name}")
                return None
                
            # Parse JSON string back to dict
            state = json.loads(state_json)
            
            return state
        except Exception as e:
            logger.error(f"Failed to retrieve agent state: {e}")
            return None
            
    def _fallback_persist(self, conversation_id: str, state: Dict[str, Any]) -> bool:
        """Fallback persistence to file system when Redis is unavailable"""
        try:
            os.makedirs("data/conversations", exist_ok=True)
            
            with open(f"data/conversations/{conversation_id}.json", "w") as f:
                json.dump(state, f)
                
            logger.info(f"Persisted conversation {conversation_id} to file system")
            return True
        except Exception as e:
            logger.error(f"Fallback persistence failed: {e}")
            return False
            
    def _fallback_retrieve(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fallback retrieval from file system when Redis is unavailable"""
        try:
            file_path = f"data/conversations/{conversation_id}.json"
            
            if not os.path.exists(file_path):
                logger.warning(f"No state file found for conversation {conversation_id}")
                return None
                
            with open(file_path, "r") as f:
                state = json.load(f)
                
            logger.info(f"Retrieved conversation {conversation_id} from file system")
            return state
        except Exception as e:
            logger.error(f"Fallback retrieval failed: {e}")
            return None
            
    async def list_conversations(self) -> List[str]:
        """List all active conversation IDs"""
        if not self.redis:
            # Fallback to file system
            try:
                if not os.path.exists("data/conversations"):
                    return []
                    
                return [
                    f.replace(".json", "") 
                    for f in os.listdir("data/conversations") 
                    if f.endswith(".json")
                ]
            except Exception:
                return []
                
        try:
            # Get all keys matching the conversation pattern
            keys = self.redis.keys("conversation:*")
            
            # Extract conversation IDs
            return [k.decode('utf-8').split(':', 1)[1] for k in keys]
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
            
    def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
