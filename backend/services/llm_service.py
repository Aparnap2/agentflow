"""
Modular LLM service with multiple providers and fallback mechanisms
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from loguru import logger
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
load_dotenv(env_path)

class LLMProvider(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    MOCK = "mock"

@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    confidence: float
    cost: float
    tokens_used: int
    response_time: float
    metadata: Dict[str, Any] = None

class LLMService:
    """Modular LLM service with fallback providers and error handling"""
    
    def __init__(self):
        self.providers = {
            LLMProvider.OPENROUTER: self._openrouter_call,
            LLMProvider.OPENAI: self._openai_call,
            LLMProvider.GOOGLE: self._google_call,
            LLMProvider.MOCK: self._mock_call,
        }
        
        # Configuration
        self.config = {
            LLMProvider.OPENROUTER: {
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1/chat/completions",
                "models": ["deepseek/deepseek-chat", "meta-llama/llama-3.1-8b-instruct:free", "microsoft/phi-3-mini-128k-instruct:free"]
            },
            LLMProvider.OPENAI: {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": "https://api.openai.com/v1/chat/completions",
                "models": ["gpt-3.5-turbo", "gpt-4o-mini"]
            },
            LLMProvider.GOOGLE: {
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
                "models": ["gemini-pro"]
            },
            LLMProvider.MOCK: {
                "api_key": "mock-key",
                "base_url": "mock://localhost",
                "models": ["mock-model"]
            }
        }
        
        # Rate limiting
        self.rate_limits = {}
        self.last_calls = {}
        
        # Health monitoring
        self.provider_health = {provider: True for provider in LLMProvider}
        
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        agent_name: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        preferred_provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """Generate response with automatic fallback"""
        
        # Determine provider order
        provider_order = self._get_provider_order(preferred_provider)
        
        last_error = None
        for provider in provider_order:
            try:
                if not self._is_provider_available(provider):
                    logger.warning(f"Provider {provider.value} unavailable, trying next")
                    continue
                
                # Rate limiting check
                if not self._check_rate_limit(provider):
                    logger.warning(f"Rate limit exceeded for {provider.value}")
                    continue
                
                start_time = datetime.now()
                
                # Call provider
                response = await self.providers[provider](
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    agent_name=agent_name
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Create response object
                llm_response = LLMResponse(
                    content=response["content"],
                    provider=provider,
                    model=response["model"],
                    confidence=response.get("confidence", 0.8),
                    cost=response.get("cost", 0.0),
                    tokens_used=response.get("tokens_used", 0),
                    response_time=response_time,
                    metadata=response.get("metadata", {})
                )
                
                # Update rate limiting
                self._update_rate_limit(provider)
                
                logger.info(f"Successfully generated response using {provider.value}")
                return llm_response
                
            except Exception as e:
                last_error = e
                logger.error(f"Provider {provider.value} failed: {str(e)}")
                self._mark_provider_unhealthy(provider)
                continue
        
        # All providers failed
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    def _get_provider_order(self, preferred: Optional[LLMProvider]) -> List[LLMProvider]:
        """Get provider order with preferred first"""
        available_providers = [p for p in LLMProvider if self._is_provider_available(p)]
        
        if preferred and preferred in available_providers:
            order = [preferred]
            order.extend([p for p in available_providers if p != preferred])
            return order
        
        # Default order by reliability (mock first for testing)
        default_order = [
            LLMProvider.MOCK,
            LLMProvider.OPENROUTER,
            LLMProvider.OPENAI,
            LLMProvider.GOOGLE,
        ]
        
        return [p for p in default_order if p in available_providers]
    
    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if provider is available"""
        config = self.config.get(provider, {})
        return (
            config.get("api_key") is not None and
            self.provider_health.get(provider, False)
        )
    
    def _check_rate_limit(self, provider: LLMProvider) -> bool:
        """Check if provider is within rate limits"""
        last_call = self.last_calls.get(provider)
        if not last_call:
            return True
        
        # Simple rate limiting - 1 call per second
        return (datetime.now() - last_call).total_seconds() >= 1.0
    
    def _update_rate_limit(self, provider: LLMProvider):
        """Update rate limit tracking"""
        self.last_calls[provider] = datetime.now()
    
    def _mark_provider_unhealthy(self, provider: LLMProvider):
        """Mark provider as unhealthy temporarily"""
        self.provider_health[provider] = False
        # Reset health after 5 minutes
        asyncio.create_task(self._reset_provider_health(provider))
    
    async def _reset_provider_health(self, provider: LLMProvider):
        """Reset provider health after timeout"""
        await asyncio.sleep(300)  # 5 minutes
        self.provider_health[provider] = True
        logger.info(f"Reset health status for {provider.value}")
    
    async def _openrouter_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> Dict[str, Any]:
        """OpenRouter API call"""
        config = self.config[LLMProvider.OPENROUTER]
        
        # Select model based on agent type
        model = self._select_model_for_agent(agent_name, config["models"])
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agentflow.ai",
            "X-Title": "AgentFlow"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["base_url"],
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "confidence": 0.8,
                "cost": 0.0,
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "metadata": {"provider": "openrouter"}
            }
    
    async def _openai_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> Dict[str, Any]:
        """OpenAI API call"""
        config = self.config[LLMProvider.OPENAI]
        
        model = self._select_model_for_agent(agent_name, config["models"])
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["base_url"],
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "confidence": 0.9,
                "cost": 0.0,
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "metadata": {"provider": "openai"}
            }
    
    async def _google_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> Dict[str, Any]:
        """Google Gemini API call"""
        config = self.config[LLMProvider.GOOGLE]
        
        # Convert messages to Google format
        text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        url = f"{config['base_url']}/gemini-pro:generateContent?key={config['api_key']}"
        
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": min(max_tokens, 8192)  # Gemini limit
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                content = "Sorry, I couldn't generate a response."
            
            return {
                "content": content,
                "model": "gemini-pro",
                "confidence": 0.7,
                "cost": 0.0,
                "tokens_used": 0,
                "metadata": {"provider": "google"}
            }
    
    async def _mock_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> Dict[str, Any]:
        """Mock LLM call for testing"""
        import random
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Generate a mock response based on agent type
        agent_responses = {
            "cofounder": "As your AI co-founder, I understand you want to develop a comprehensive business plan. Let me guide you through the key questions to create a strategic roadmap for your venture.",
            "manager": "I'll coordinate the team and ensure all agents work together efficiently to deliver your business plan. Let me assign tasks to our specialists.",
            "product": "For your product strategy, I recommend focusing on MVP development, user personas, and market validation. Here's a structured approach...",
            "finance": "Based on initial analysis, I project strong financial potential. Let me create detailed financial models and projections.",
            "marketing": "Your marketing strategy should focus on digital channels and customer acquisition. Here's my recommended approach...",
            "legal": "From a legal perspective, we need to address compliance, intellectual property, and business structure. Here are the key considerations...",
            "default": f"Hello! I'm the {agent_name} agent. I've analyzed your request and here's my expert response based on my specialized knowledge and experience."
        }
        
        user_message = messages[-1]["content"] if messages else ""
        base_response = agent_responses.get(agent_name.lower(), agent_responses["default"])
        
        # Add context-aware response
        if "business plan" in user_message.lower():
            context_response = f" I'll help you create a comprehensive business plan with detailed analysis and recommendations."
        elif "startup" in user_message.lower():
            context_response = f" Your startup idea has great potential. Let me provide strategic insights."
        else:
            context_response = f" I'm ready to assist with your project requirements."
        
        mock_response = base_response + context_response
        
        return {
            "content": mock_response,
            "model": "mock-model",
            "confidence": round(random.uniform(0.75, 0.95), 2),
            "cost": 0.0,
            "tokens_used": len(mock_response.split()),
            "metadata": {"provider": "mock", "test_mode": True}
        }
    
    def _select_model_for_agent(self, agent_name: str, available_models: List[str]) -> str:
        """Select appropriate model based on agent type"""
        # Strategic agents need more capable models
        strategic_agents = ["cofounder", "manager", "product"]
        
        if agent_name.lower() in strategic_agents:
            # Use best available model
            return available_models[0]
        else:
            # Use efficient model for routine tasks
            return available_models[-1] if len(available_models) > 1 else available_models[0]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            "providers": {
                provider.value: {
                    "healthy": self.provider_health[provider],
                    "available": self._is_provider_available(provider),
                    "configured": self.config.get(provider, {}).get("api_key") is not None
                }
                for provider in LLMProvider
            },
            "last_updated": datetime.now().isoformat()
        }

# Global service instance
llm_service = LLMService()
