"""
ContextManager - Enhanced context retrieval and reasoning
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from loguru import logger

from memory.memory_manager import MemoryManager
from memory.vector_memory import VectorMemory
from memory.graph_memory import GraphMemory

class ContextManager:
    """Advanced context management with semantic search and relevance ranking"""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        vector_memory: Optional[VectorMemory] = None,
        graph_memory: Optional[GraphMemory] = None
    ):
        """Initialize context manager
        
        Args:
            memory_manager: Memory manager for retrieving agent memory
            vector_memory: Optional vector memory for semantic search
            graph_memory: Optional graph memory for relationships
        """
        self.memory_manager = memory_manager
        self.vector_memory = vector_memory
        self.graph_memory = graph_memory
    
    async def get_relevant_context(
        self,
        query: str,
        agent_name: Optional[str] = None,
        task_type: Optional[str] = None,
        max_items: int = 10,
        include_shared: bool = True,
        min_relevance: float = 0.7
    ) -> Dict[str, Any]:
        """Get relevant context for a query
        
        Args:
            query: Query text to find relevant context for
            agent_name: Optional agent to filter context by
            task_type: Optional task type to filter context by
            max_items: Maximum number of context items to return
            include_shared: Whether to include shared memory
            min_relevance: Minimum relevance score (0-1)
            
        Returns:
            Dict[str, Any]: Structured relevant context
        """
        context = {
            "relevant_items": [],
            "agent_context": {},
            "task_context": {},
            "relationships": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Get semantic search results if vector memory is available
        semantic_results = []
        if self.vector_memory:
            try:
                semantic_results = await self.vector_memory.semantic_search(
                    query=query,
                    agent=agent_name,
                    limit=max_items
                )
                
                # Add to relevant items
                for result in semantic_results:
                    if result.get("score", 0) >= min_relevance:
                        context["relevant_items"].append({
                            "content": result.get("text", ""),
                            "source": "semantic_search",
                            "agent": result.get("agent"),
                            "relevance": result.get("score", 0),
                            "metadata": result.get("metadata", {})
                        })
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
        
        # Get agent-specific context
        if agent_name:
            try:
                # Query agent private memory
                agent_memories = await self.memory_manager.query_agent_memory(
                    agent_name=agent_name,
                    limit=max_items
                )
                
                context["agent_context"] = {
                    "agent": agent_name,
                    "memories": agent_memories
                }
                
                # Add relevant items from agent memories
                for memory in agent_memories:
                    context["relevant_items"].append({
                        "content": str(memory.get("content", {})),
                        "source": "agent_memory",
                        "agent": agent_name,
                        "type": memory.get("type"),
                        "relevance": 0.9,  # High relevance for agent's own memories
                        "timestamp": memory.get("timestamp")
                    })
            except Exception as e:
                logger.error(f"Failed to get agent context: {e}")
        
        # Get task-specific context if task_type is provided
        if task_type:
            try:
                # Query shared memory for task type
                task_memories = []
                shared_context = await self.memory_manager.get_shared_context()
                
                for item in shared_context:
                    item_content = item.get("content", {})
                    if isinstance(item_content, dict) and item_content.get("task_type") == task_type:
                        task_memories.append(item)
                
                context["task_context"] = {
                    "task_type": task_type,
                    "memories": task_memories[:max_items]
                }
                
                # Add relevant items from task memories
                for memory in task_memories[:max_items]:
                    context["relevant_items"].append({
                        "content": str(memory.get("content", {})),
                        "source": "task_memory",
                        "type": memory.get("type"),
                        "relevance": 0.85,  # High relevance for task-specific memories
                        "timestamp": memory.get("timestamp")
                    })
            except Exception as e:
                logger.error(f"Failed to get task context: {e}")
        
        # Get shared context if requested
        if include_shared:
            try:
                shared_context = await self.memory_manager.get_shared_context()
                
                # Add most recent shared memories
                recent_shared = sorted(
                    shared_context,
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )[:max_items]
                
                for memory in recent_shared:
                    # Skip if already added from task or agent context
                    if any(item.get("content") == str(memory.get("content", {})) 
                           for item in context["relevant_items"]):
                        continue
                    
                    context["relevant_items"].append({
                        "content": str(memory.get("content", {})),
                        "source": "shared_memory",
                        "agent": memory.get("agent"),
                        "type": memory.get("type"),
                        "relevance": 0.7,  # Medium relevance for shared memories
                        "timestamp": memory.get("timestamp")
                    })
            except Exception as e:
                logger.error(f"Failed to get shared context: {e}")
        
        # Get relationship data if graph memory is available
        if self.graph_memory and agent_name:
            try:
                graph_context = await self.graph_memory.get_agent_context(
                    agent_name=agent_name,
                    depth=2
                )
                
                if graph_context and "recent_outputs" in graph_context:
                    context["relationships"] = graph_context["recent_outputs"]
            except Exception as e:
                logger.error(f"Failed to get graph relationships: {e}")
        
        # Sort relevant items by relevance score
        context["relevant_items"] = sorted(
            context["relevant_items"], 
            key=lambda x: x.get("relevance", 0), 
            reverse=True
        )
        
        # Limit to max_items
        context["relevant_items"] = context["relevant_items"][:max_items]
        
        return context
    
    async def enrich_task_context(
        self, 
        task: Dict[str, Any],
        agent_name: str
    ) -> Dict[str, Any]:
        """Enrich a task with relevant context
        
        Args:
            task: Task data to enrich
            agent_name: Agent processing the task
            
        Returns:
            Dict[str, Any]: Task with enriched context
        """
        # Create a copy of the task to enrich
        enriched_task = dict(task)
        
        # Extract task description for context search
        task_description = ""
        if "description" in task:
            task_description = task["description"]
        elif "type" in task:
            task_description = task["type"]
        elif "id" in task:
            task_description = task["id"]
        
        # Get relevant context based on task description
        context = await self.get_relevant_context(
            query=task_description,
            agent_name=agent_name,
            task_type=task.get("type"),
            max_items=5,
            include_shared=True
        )
        
        # Add context to task
        enriched_task["context"] = context
        
        # Add any related task history if available
        if "id" in task and self.memory_manager:
            try:
                task_history = await self.memory_manager.query_shared_memory(
                    memory_type=f"task_{task['id']}",
                    limit=3
                )
                
                if task_history:
                    enriched_task["task_history"] = task_history
            except Exception as e:
                logger.error(f"Failed to get task history: {e}")
        
        return enriched_task
    
    async def get_working_memory(
        self,
        agent_name: str,
        current_task: Optional[Dict[str, Any]] = None,
        max_items: int = 10
    ) -> Dict[str, Any]:
        """Get working memory for an agent
        
        Args:
            agent_name: Agent name
            current_task: Optional current task
            max_items: Maximum number of memory items to include
            
        Returns:
            Dict[str, Any]: Working memory
        """
        working_memory = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "recent_private": [],
            "recent_shared": [],
            "related_context": []
        }
        
        # Get recent private memories
        try:
            private_memories = await self.memory_manager.query_agent_memory(
                agent_name=agent_name,
                limit=max_items
            )
            
            working_memory["recent_private"] = private_memories
        except Exception as e:
            logger.error(f"Failed to get private memories: {e}")
        
        # Get recent shared memories
        try:
            shared_memories = await self.memory_manager.query_shared_memory(
                min_confidence=0.7,
                limit=max_items
            )
            
            working_memory["recent_shared"] = [
                memory for memory in shared_memories
                if memory.get("author") != agent_name  # Only include other agents' shared memories
            ]
        except Exception as e:
            logger.error(f"Failed to get shared memories: {e}")
        
        # If current task is provided, get related context
        if current_task:
            try:
                task_description = current_task.get("description", "") or current_task.get("type", "")
                
                related_context = await self.get_relevant_context(
                    query=task_description,
                    agent_name=None,  # Don't filter by agent
                    task_type=current_task.get("type"),
                    max_items=max_items,
                    include_shared=True
                )
                
                working_memory["related_context"] = related_context["relevant_items"]
            except Exception as e:
                logger.error(f"Failed to get related context: {e}")
        
        return working_memory
