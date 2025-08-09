"""
DynamicToolSelector - Context-aware tool selection based on task requirements
"""

from typing import Dict, List, Any, Optional
import re
from loguru import logger
from langchain.tools import BaseTool

from tools.tool_registry import ToolRegistry

class DynamicToolSelector:
    """Selects optimal tools based on task and context"""
    
    def __init__(self, tool_registry: ToolRegistry):
        """Initialize dynamic tool selector
        
        Args:
            tool_registry: Tool registry containing available tools
        """
        self.tool_registry = tool_registry
        self.tool_usage_stats = {}
        
    async def select_tools_for_task(
        self, 
        task: Dict[str, Any], 
        context: Dict[str, Any],
        agent_name: str,
        max_tools: int = 5
    ) -> List[BaseTool]:
        """Select the best tools for a given task and context
        
        Args:
            task: Task to select tools for
            context: Context information
            agent_name: Name of the agent performing the task
            max_tools: Maximum number of tools to select
            
        Returns:
            List[BaseTool]: Selected tools for the task
        """
        # Extract task details
        task_type = task.get("type", "")
        task_description = task.get("description", "")
        
        # Extract keywords from task
        keywords = self._extract_keywords(task_type, task_description)
        
        # Get agent's default tools
        default_tools = self.tool_registry.get_tools_for_agent(agent_name)
        
        # Filter tools by relevance to task
        relevant_tools = []
        all_tools = self.tool_registry.get_all_tools()
        
        for tool_name, tool in all_tools.items():
            # Skip if tool is already in default tools
            if tool in default_tools:
                continue
                
            # Calculate relevance score based on keyword matches
            relevance = self._calculate_tool_relevance(tool, keywords)
            
            if relevance > 0.3:  # Threshold for considering a tool
                relevant_tools.append((tool, relevance))
        
        # Sort by relevance
        relevant_tools.sort(key=lambda x: x[1], reverse=True)
        
        # Select top tools by relevance
        additional_tools = [tool for tool, _ in relevant_tools[:max_tools - len(default_tools)]]
        
        # Combine default and additional tools
        selected_tools = default_tools + additional_tools
        
        # Limit to max_tools
        selected_tools = selected_tools[:max_tools]
        
        # Log selection
        tool_names = [tool.name for tool in selected_tools]
        logger.info(f"Selected tools for {agent_name} on {task_type}: {', '.join(tool_names)}")
        
        # Update usage statistics
        for tool in selected_tools:
            if tool.name not in self.tool_usage_stats:
                self.tool_usage_stats[tool.name] = 0
            self.tool_usage_stats[tool.name] += 1
        
        return selected_tools
    
    def _extract_keywords(self, task_type: str, description: str) -> List[str]:
        """Extract keywords from task description
        
        Args:
            task_type: Type of task
            description: Task description
            
        Returns:
            List[str]: List of keywords
        """
        # Combine task type and description
        text = f"{task_type} {description}".lower()
        
        # Remove punctuation and split by spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Remove common stopwords
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 
                    'were', 'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for',
                    'with', 'by', 'about', 'as', 'of', 'that', 'this', 'these',
                    'those', 'it', 'its', 'task', 'should', 'would', 'could'}
        
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Add the task type as a keyword if not already included
        if task_type.lower() not in keywords:
            keywords.append(task_type.lower())
            
        return keywords
    
    def _calculate_tool_relevance(self, tool: BaseTool, keywords: List[str]) -> float:
        """Calculate relevance of a tool to keywords
        
        Args:
            tool: Tool to calculate relevance for
            keywords: List of task keywords
            
        Returns:
            float: Relevance score (0-1)
        """
        # Extract tool description and name keywords
        tool_text = f"{tool.name} {tool.description}".lower()
        
        # Count keyword matches
        matches = 0
        for keyword in keywords:
            if keyword in tool_text:
                matches += 1
        
        # Calculate relevance score
        if not keywords:
            return 0.0
            
        relevance = matches / len(keywords)
        
        # Boost for frequently used tools
        usage_boost = 0.0
        if tool.name in self.tool_usage_stats:
            usage_count = self.tool_usage_stats[tool.name]
            usage_boost = min(0.2, usage_count / 10)  # Max 0.2 boost for frequently used tools
        
        return min(1.0, relevance + usage_boost)
    
    async def get_recommended_tools(
        self,
        query: str,
        agent_name: Optional[str] = None,
        max_tools: int = 3
    ) -> List[BaseTool]:
        """Get recommended tools based on a query
        
        Args:
            query: Query text
            agent_name: Optional agent name to filter tools
            max_tools: Maximum number of tools to recommend
            
        Returns:
            List[BaseTool]: Recommended tools
        """
        # Extract keywords from query
        keywords = self._extract_keywords("", query)
        
        # Get available tools
        if agent_name:
            available_tools = self.tool_registry.get_tools_for_agent(agent_name)
        else:
            available_tools = list(self.tool_registry.get_all_tools().values())
        
        # Calculate relevance for each tool
        tool_relevance = []
        for tool in available_tools:
            relevance = self._calculate_tool_relevance(tool, keywords)
            tool_relevance.append((tool, relevance))
        
        # Sort by relevance
        tool_relevance.sort(key=lambda x: x[1], reverse=True)
        
        # Return top tools
        return [tool for tool, _ in tool_relevance[:max_tools]]
    
    def get_usage_statistics(self) -> Dict[str, int]:
        """Get tool usage statistics
        
        Returns:
            Dict[str, int]: Tool usage counts
        """
        return self.tool_usage_stats
