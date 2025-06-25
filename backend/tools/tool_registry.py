from typing import Dict, List, Any, Callable
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
from loguru import logger

class ToolRegistry:
    """Registry for agent tools as specified in PRD"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.tools = {}
        self._register_common_tools()
        self._register_agent_specific_tools()
    
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
    
    def _create_tool(self, tool_name: str) -> BaseTool:
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
        return tool_map.get(tool_name, BaseTool())
    
    def get_tools(self) -> List[BaseTool]:
        """Get all available tools for this agent"""
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> BaseTool:
        """Get specific tool by name"""
        return self.tools.get(name)

# Tool implementations
class MemoryWriteTool(BaseTool):
    name = "memory_write"
    description = "Write to agent memory"
    
    def _run(self, content: str, memory_type: str = "general") -> str:
        # Implementation would integrate with GraphMemory
        return f"Stored {memory_type} memory: {content[:50]}..."

class MemoryQueryTool(BaseTool):
    name = "memory_query"
    description = "Query agent memory"
    
    def _run(self, query: str, memory_type: str = None) -> str:
        # Implementation would query GraphMemory
        return f"Memory query results for: {query}"

class LLMReasoningTool(BaseTool):
    name = "llm_reasoning"
    description = "Use LLM for reasoning via OpenRouter"
    
    def _run(self, prompt: str, model: str = "anthropic/claude-3-haiku") -> str:
        # Implementation would call OpenRouter API
        return f"LLM response to: {prompt[:50]}..."

class MemoryReadAllTool(BaseTool):
    name = "memory_read_all"
    description = "Read all shared memory (Manager only)"
    
    def _run(self) -> str:
        return "All shared memory contents..."

class TaskAssignTool(BaseTool):
    name = "task_assign"
    description = "Assign task to agent (Manager only)"
    
    def _run(self, agent: str, task: str) -> str:
        return f"Assigned task to {agent}: {task}"

class WorkflowGenerateTool(BaseTool):
    name = "workflow_generate"
    description = "Generate workflow graph (Manager only)"
    
    def _run(self, requirements: str) -> str:
        return f"Generated workflow for: {requirements}"

class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "Search Qdrant vector database"
    
    def _run(self, query: str) -> str:
        return f"RAG search results for: {query}"

class PersonaCreateTool(BaseTool):
    name = "persona_create"
    description = "Create user persona (Product only)"
    
    def _run(self, description: str) -> str:
        return f"Created persona: {description}"

class JSONExportTool(BaseTool):
    name = "json_export"
    description = "Export data to JSON format"
    
    def _run(self, data: dict) -> str:
        return json.dumps(data, indent=2)

class FinanceAPITool(BaseTool):
    name = "api_finance_call"
    description = "Mock finance API call"
    
    def _run(self, endpoint: str) -> str:
        return f"Finance API response from {endpoint}"

class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch web content using Crawl4AI"
    
    def _run(self, url: str) -> str:
        return f"Web content from {url}"

class MemoryCrossQueryTool(BaseTool):
    name = "memory_cross_query"
    description = "Query across all agent memories"
    
    def _run(self, query: str) -> str:
        return f"Cross-agent memory results: {query}"

class SocialCrawlTool(BaseTool):
    name = "web_crawl_social"
    description = "Crawl social media content"
    
    def _run(self, platform: str) -> str:
        return f"Social content from {platform}"

class ContentGenerateTool(BaseTool):
    name = "content_generate"
    description = "Generate marketing content"
    
    def _run(self, content_type: str, topic: str) -> str:
        return f"Generated {content_type} about {topic}"

class SEOKeywordsTool(BaseTool):
    name = "seo_keywords"
    description = "Suggest SEO keywords"
    
    def _run(self, topic: str) -> str:
        return f"SEO keywords for {topic}"

class TOSTemplateTool(BaseTool):
    name = "template_generate_tos"
    description = "Generate Terms of Service template"
    
    def _run(self, company_type: str) -> str:
        return f"TOS template for {company_type}"

class ComplianceCheckTool(BaseTool):
    name = "compliance_check"
    description = "Check compliance flags"
    
    def _run(self, content: str) -> str:
        return f"Compliance check for content"