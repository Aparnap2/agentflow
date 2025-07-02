from typing import Dict, List, Any, Callable
from langchain.tools import BaseTool as LCBaseTool # Rename to avoid conflict
from pydantic import BaseModel, Field
import json
import os
import httpx
from loguru import logger


class ToolRegistry:
    """Registry for agent tools as specified in PRD"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.tools = {}
        self._register_common_tools()
        self._register_agent_specific_tools()
        # OpenRouter API will be configured per request
    
    def _register_common_tools(self):
        """Register tools available to all agents"""
        self.tools.update({
            "memory_write": MemoryWriteTool(),
            "memory_query": MemoryQueryTool(),
            "llm_reasoning": LLMReasoningTool()
        })
    
    def _register_agent_specific_tools(self):
        """Register tools specific to each agent type"""
        agent_tools = {
            "Cofounder": ["memory_write", "memory_query", "llm_reasoning"],
            "Manager": ["memory_read_all", "task_assign", "workflow_generate"],
            "Product": ["rag_search", "persona_create", "json_export"],
            "Finance": ["api_finance_call", "web_fetch", "memory_cross_query"],
            "Marketing": ["web_crawl_social", "content_generate", "seo_keywords"],
            "Legal": ["template_generate_tos", "compliance_check"]
        }
        
        if self.agent_name in agent_tools:
            for tool_name in agent_tools[self.agent_name]:
                if tool_name not in self.tools:
                    self.tools[tool_name] = self._create_tool(tool_name)
    
    def _create_tool(self, tool_name: str) -> LCBaseTool:
        """Factory method to create tools"""
        tool_map = {
            "memory_read_all": MemoryReadAllTool(),
            "task_assign": TaskAssignTool(),
            "workflow_generate": WorkflowGenerateTool(),
            "rag_search": RAGSearchTool(),
            "persona_create": PersonaCreateTool(),
            "json_export": JSONExportTool(),
            "api_finance_call": FinanceAPITool(),
            "web_fetch": WebFetchTool(),
            "memory_cross_query": MemoryCrossQueryTool(),
            "web_crawl_social": SocialCrawlTool(),
            "content_generate": ContentGenerateTool(),
            "seo_keywords": SEOKeywordsTool(),
            "template_generate_tos": TOSTemplateTool(),
            "compliance_check": ComplianceCheckTool()
        }
        return tool_map.get(tool_name)
    
    def get_tools(self) -> List[LCBaseTool]:
        """Get list of all registered tools for this agent"""
        return list(self.tools.values())
        
    def get_tools_for_agent(self, agent_name: str) -> List[LCBaseTool]:
        """Get tools for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List[LCBaseTool]: List of tools for the agent
        """
        if agent_name == self.agent_name:
            return self.get_tools()
            
        # For other agents, create a new ToolRegistry instance
        registry = ToolRegistry(agent_name)
        return registry.get_tools()
        
    def get_all_tools(self) -> Dict[str, LCBaseTool]:
        """Get all registered tools
        
        Returns:
            Dict[str, LCBaseTool]: Dictionary of tool name to tool
        """
        return self.tools
    
    def get_tool(self, name: str) -> LCBaseTool:
        """Get specific tool by name"""
        return self.tools.get(name)

# Tool implementations
class MemoryWriteTool(LCBaseTool):
    name: str = "memory_write"
    description: str = "Write to agent memory"
    
    def _run(self, content: str, memory_type: str = "general") -> str:
        # Implementation would integrate with GraphMemory
        return f"Stored {memory_type} memory: {content[:50]}..."
    
    async def _arun(self, content: str, memory_type: str = "general") -> str:
        # Implementation would integrate with GraphMemory
        return f"Stored {memory_type} memory: {content[:50]}..."

class MemoryQueryTool(LCBaseTool):
    name: str = "memory_query"
    description: str = "Query agent memory"
    
    def _run(self, query: str, memory_type: str = None) -> str:
        # Implementation would query GraphMemory
        return f"Memory query results for: {query}"
    
    async def _arun(self, query: str, memory_type: str = None) -> str:
        # Implementation would query GraphMemory
        return f"Memory query results for: {query}"

class LLMReasoningTool(LCBaseTool):
    name: str = "llm_reasoning"
    description: str = "Use LLM for reasoning via OpenRouter"
    
    def _run(self, prompt: str, model_name: str = "deepseek/deepseek-chat:free") -> str:
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return "Error: OPENROUTER_API_KEY not set"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            with httpx.Client() as client:
                response = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return f"Error: LLM reasoning failed - {str(e)}"
    
    async def _arun(self, prompt: str, model_name: str = "deepseek/deepseek-chat:free") -> str:
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return "Error: OPENROUTER_API_KEY not set"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return f"Error: LLM reasoning failed - {str(e)}"

class MemoryReadAllTool(LCBaseTool):
    name: str = "memory_read_all"
    description: str = "Read all shared memory (Manager only)"
    
    def _run(self) -> str:
        return "All shared memory contents..."
    
    async def _arun(self) -> str:
        return "All shared memory contents..."

class TaskAssignTool(LCBaseTool):
    name: str = "task_assign"
    description: str = "Assign task to agent (Manager only)"
    
    def _run(self, agent: str, task: str) -> str:
        return f"Assigned task to {agent}: {task}"
    
    async def _arun(self, agent: str, task: str) -> str:
        return f"Assigned task to {agent}: {task}"

class WorkflowGenerateTool(LCBaseTool):
    name: str = "workflow_generate"
    description: str = "Generate workflow graph (Manager only)"
    
    def _run(self, requirements: str) -> str:
        return f"Generated workflow for: {requirements}"
    
    async def _arun(self, requirements: str) -> str:
        return f"Generated workflow for: {requirements}"

class RAGSearchTool(LCBaseTool):
    name: str = "rag_search"
    description: str = "Search Qdrant vector database"
    
    def _run(self, query: str) -> str:
        return f"RAG search results for: {query}"
    
    async def _arun(self, query: str) -> str:
        from memory.vector_memory import VectorMemory # Import locally to avoid circular dependency
        vector_memory = VectorMemory()
        results = await vector_memory.semantic_search(query=query)
        if results:
            # Return a simplified string representation of the results
            return json.dumps([{"text": r["text"], "score": r["score"]} for r in results])
        return "No relevant documents found."

class PersonaCreateTool(LCBaseTool):
    name: str = "persona_create"
    description: str = "Create user persona (Product only)"
    
    def _run(self, description: str) -> str:
        return f"Created persona: {description}"
    
    async def _arun(self, description: str) -> str:
        return f"Created persona: {description}"

class JSONExportTool(LCBaseTool):
    name: str = "json_export"
    description: str = "Export data to JSON format"
    
    def _run(self, data: dict) -> str:
        return json.dumps(data, indent=2)
    
    async def _arun(self, data: dict) -> str:
        return json.dumps(data, indent=2)

class FinanceAPITool(LCBaseTool):
    name: str = "api_finance_call"
    description: str = "Mock finance API call"
    
    def _run(self, endpoint: str) -> str:
        return f"Finance API response from {endpoint}"
    
    async def _arun(self, endpoint: str) -> str:
        return f"Finance API response from {endpoint}"

class WebFetchTool(LCBaseTool):
    name: str = "web_fetch"
    description: str = "Fetch web content using Crawl4AI"
    
    def _run(self, url: str) -> str:
        return f"Web content from {url}"
    
    async def _arun(self, url: str) -> str:
        return f"Web content from {url}"

class MemoryCrossQueryTool(LCBaseTool):
    name: str = "memory_cross_query"
    description: str = "Query across all agent memories"
    
    def _run(self, query: str) -> str:
        return f"Cross-agent memory results: {query}"
    
    async def _arun(self, query: str) -> str:
        return f"Cross-agent memory results: {query}"

class SocialCrawlTool(LCBaseTool):
    name: str = "web_crawl_social"
    description: str = "Crawl social media content"
    
    def _run(self, platform: str) -> str:
        return f"Social content from {platform}"
    
    async def _arun(self, platform: str) -> str:
        return f"Social content from {platform}"

class ContentGenerateTool(LCBaseTool):
    name: str = "content_generate"
    description: str = "Generate marketing content"
    
    def _run(self, content_type: str, topic: str) -> str:
        return f"Generated {content_type} about {topic}"
    
    async def _arun(self, content_type: str, topic: str) -> str:
        return f"Generated {content_type} about {topic}"

class SEOKeywordsTool(LCBaseTool):
    name: str = "seo_keywords"
    description: str = "Suggest SEO keywords"
    
    def _run(self, topic: str) -> str:
        return f"SEO keywords for {topic}"
    
    async def _arun(self, topic: str) -> str:
        return f"SEO keywords for {topic}"

class TOSTemplateTool(LCBaseTool):
    name: str = "template_generate_tos"
    description: str = "Generate Terms of Service template"
    
    def _run(self, company_type: str) -> str:
        return f"TOS template for {company_type}"
    
    async def _arun(self, company_type: str) -> str:
        return f"TOS template for {company_type}"

class ComplianceCheckTool(LCBaseTool):
    name: str = "compliance_check"
    description: str = "Check compliance flags"
    
    def _run(self, content: str) -> str:
        return f"Compliance check for content"
    
    async def _arun(self, content: str) -> str:
        return f"Compliance check for content"