import asyncio
from typing import Any, Callable, Dict, Optional
from loguru import logger

class EventCacheManager:
    """Manages event-driven caching and invalidation."""
    
    def __init__(self):
        self._event_listeners = {}
        self._cache_data = {}

    async def get_cached_data(self, key: str, fetch_func: Callable[[], Any]) -> Optional[Any]:
        """Retrieves data from cache or fetches it if not present."""
        if key in self._cache_data:
            return self._cache_data[key]
        
        data = await fetch_func()
        self._cache_data[key] = data
        return data

    async def cache_shared_context(self, context_type: str, content: Dict[str, Any], confidence: float) -> None:
        """Caches shared context data."""
        cache_key = f"shared_context:{context_type}:{confidence}"
        self._cache_data[cache_key] = content
        logger.info(f"Cached shared context: {cache_key}")
