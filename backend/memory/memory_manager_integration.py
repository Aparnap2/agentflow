"""
Memory Manager Integration - Integrates new memory optimization components
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from .context_pruner import ContextPruner
from .memory_compressor import MemoryCompressor
from .optimized_vector_search import OptimizedVectorSearch
from .shared_context_manager import SharedContextManager

class MemoryManagerIntegration:
    """Integrates memory optimization components with the existing memory manager"""
    
    def __init__(self, memory_manager, llm_service=None):
        self.memory_manager = memory_manager
        self.context_pruner = ContextPruner(max_tokens=4000)
        self.memory_compressor = MemoryCompressor(llm_service)
        self.vector_search = OptimizedVectorSearch(memory_manager.vector_memory)
        self.shared_context_manager = SharedContextManager(memory_manager)
    
    async def get_optimized_context(self, agent_name: str, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """Get optimized context for an agent based on query"""
        # Get global context
        global_context = await self.memory_manager.get_global_context_for_agent(agent_name, query)
        
        # Get agent's private memory
        private_memories = await self.memory_manager.get_agent_private_memory(agent_name)
        
        # Compress memories if there are too many
        if len(private_memories) > 10:
            private_memories = await self.memory_compressor.compress_memories(private_memories, max_items=5)
        
        # Combine context
        full_context = {
            "agent_name": agent_name,
            "query": query,
            "global_context": global_context,
            "private_memories": private_memories
        }
        
        # Prune context to fit token limit
        pruned_context = self.context_pruner.prune_context(full_context, query)
        
        return pruned_context
    
    async def enhanced_semantic_search(self, query: str, agent_name: Optional[str] = None,
                                    memory_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Enhanced semantic search with fallback and optimization"""
        return await self.vector_search.semantic_search_with_fallback(query, agent_name, memory_type, limit)
    
    async def batch_semantic_search(self, queries: List[str], agent_name: Optional[str] = None,
                                  memory_type: Optional[str] = None, limit: int = 5) -> List[List[Dict[str, Any]]]:
        """Perform multiple semantic searches in a batch"""
        return await self.vector_search.batch_search(queries, agent_name, memory_type, limit)
    
    async def compress_agent_memories(self, agent_name: str) -> Dict[str, Any]:
        """Compress an agent's memories by type"""
        return await self.memory_compressor.compress_agent_memory(agent_name, self.memory_manager)
    
    async def store_with_compression(self, agent_name: str, memory_type: str, content: Dict[str, Any],
                                   metadata: Optional[Dict[str, Any]] = None, is_shared: bool = False,
                                   confidence: float = 1.0) -> str:
        """Store memory with compression for large content"""
        # Check if content is large and needs compression
        content_size = len(str(content))
        
        if content_size > 10000:  # 10KB threshold
            logger.info(f"Large content detected ({content_size} bytes), compressing before storage")
            
            # Create a compressed version
            if isinstance(content, dict):
                # Extract key information
                compressed_content = {
                    "original_size": content_size,
                    "compressed": True
                }
                
                # Keep important fields
                important_fields = ["id", "name", "type", "summary", "result", "confidence"]
                for field in important_fields:
                    if field in content:
                        compressed_content[field] = content[field]
                
                # Add a summary if possible
                if self.memory_compressor.llm_service:
                    try:
                        summary = await self.memory_compressor.llm_service.generate(
                            system_prompt="Summarize the following content concisely while preserving key information.",
                            user_message=str(content),
                            temperature=0.3,
                            max_tokens=200
                        )
                        compressed_content["summary"] = summary
                    except Exception as e:
                        logger.error(f"Failed to generate summary: {e}")
                        compressed_content["summary"] = f"Large content ({content_size} bytes)"
                else:
                    compressed_content["summary"] = f"Large content ({content_size} bytes)"
                
                # Store compressed content
                return await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=memory_type,
                    content=compressed_content,
                    metadata=metadata,
                    is_shared=is_shared,
                    confidence=confidence
                )
            else:
                # For non-dict content, just truncate
                truncated = str(content)[:5000] + f"... [truncated, original size: {content_size} bytes]"
                return await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=memory_type,
                    content=truncated,
                    metadata=metadata,
                    is_shared=is_shared,
                    confidence=confidence
                )
        else:
            # Content is not large, store normally
            return await self.memory_manager.store_agent_memory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content,
                metadata=metadata,
                is_shared=is_shared,
                confidence=confidence
            )
            
    # Shared Context Manager methods
    
    async def store_shared_context(self, 
                                 context_type: str, 
                                 content: Dict[str, Any],
                                 source_agent: str,
                                 access_control: Optional[Dict[str, Any]] = None,
                                 parent_version_id: Optional[str] = None,
                                 change_description: Optional[str] = None,
                                 confidence: float = 1.0) -> str:
        """Store context that should be accessible to multiple agents with role-based access control"""
        return await self.shared_context_manager.store_shared_context(
            context_type=context_type,
            content=content,
            source_agent=source_agent,
            access_control=access_control,
            parent_version_id=parent_version_id,
            change_description=change_description,
            confidence=confidence
        )
    
    async def get_shared_context(self, 
                               context_type: Optional[str] = None,
                               query: Optional[str] = None,
                               requesting_agent: Optional[str] = None,
                               version_id: Optional[str] = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Get shared context accessible to the requesting agent with role-based access control"""
        return await self.shared_context_manager.get_shared_context(
            context_type=context_type,
            query=query,
            requesting_agent=requesting_agent,
            version_id=version_id,
            limit=limit
        )
    
    async def update_shared_context(self,
                                  context_id: str,
                                  updates: Dict[str, Any],
                                  updating_agent: str,
                                  change_description: Optional[str] = None) -> Dict[str, Any]:
        """Update existing shared context with versioning and access control"""
        return await self.shared_context_manager.update_shared_context(
            context_id=context_id,
            updates=updates,
            updating_agent=updating_agent,
            change_description=change_description
        )
    
    async def get_context_history(self,
                                context_id: str,
                                requesting_agent: str,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """Get version history for a specific context with access control"""
        return await self.shared_context_manager.get_context_history(
            context_id=context_id,
            requesting_agent=requesting_agent,
            limit=limit
        )
    
    async def get_agent_specific_context(self,
                                       agent_name: str,
                                       context_type: Optional[str] = None,
                                       query: Optional[str] = None) -> Dict[str, Any]:
        """Get context specific to an agent, including relevant shared context with access control"""
        return await self.shared_context_manager.get_agent_specific_context(
            agent_name=agent_name,
            context_type=context_type,
            query=query
        )
    
    async def grant_access(self,
                         context_id: str,
                         granting_agent: str,
                         target_role: str,
                         access_type: str) -> Dict[str, Any]:
        """Grant read or write access to a role for a specific context"""
        return await self.shared_context_manager.grant_access(
            context_id=context_id,
            granting_agent=granting_agent,
            target_role=target_role,
            access_type=access_type
        )
    
    async def revoke_access(self,
                          context_id: str,
                          revoking_agent: str,
                          target_role: str,
                          access_type: str) -> Dict[str, Any]:
        """Revoke read or write access from a role for a specific context"""
        return await self.shared_context_manager.revoke_access(
            context_id=context_id,
            revoking_agent=revoking_agent,
            target_role=target_role,
            access_type=access_type
        )