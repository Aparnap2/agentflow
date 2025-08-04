"""
Base Integration Class for External APIs
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from loguru import logger


class IntegrationConfig(BaseModel):
    """Configuration for external integrations"""
    api_key: str
    base_url: str
    timeout: int = 30
    retry_attempts: int = 3


class BaseIntegration(ABC):
    """Base class for all external API integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session = None
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health and connectivity"""
        pass
        
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                # Implementation would use aiohttp or similar
                logger.info(f"Making {method} request to {endpoint}")
                return {"status": "success", "data": data}
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)