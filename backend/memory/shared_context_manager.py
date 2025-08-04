"""
Shared Context Manager - Manages shared context across agents with role-based access control
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from memory.memory_manager import OptimizedMemoryManager
from memory.event_cache_manager import EventCacheManager
from communication.event_bus import event_bus

class ContextVersion(BaseModel):
    """Model for context versioning"""
    version_id: str = Field(..., description="Unique version identifier")
    content: Dict[str, Any] = Field(..., description="Version content")
    created_by: str = Field(..., description="Agent that created this version")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    parent_version_id: Optional[str] = Field(None, description="Parent version ID")
    change_description: Optional[str] = Field(None, description="Description of changes from parent version")

class AccessControl(BaseModel):
    """Model for role-based access control"""
    read_roles: Set[str] = Field(default_factory=set, description="Roles that can read this context")
    write_roles: Set[str] = Field(default_factory=set, description="Roles that can modify this context")
    owner: str = Field(..., description="Agent that owns this context")

class SharedContextManager:
    """Manages shared context across agents with role-based access control and versioning"""
    
    def __init__(self, memory_manager: OptimizedMemoryManager):
        self.memory_manager = memory_manager
        self.event_cache_manager = EventCacheManager()
        self.context_versions = {}  # Dict[context_id, List[ContextVersion]]
        self.access_controls = {}   # Dict[context_id, AccessControl]
        
        # Default role hierarchy (higher number = more privileges)
        self.role_hierarchy = {
            "cofounder": 5,
            "manager": 4,
            "strategy": 3,
            "finance": 3,
            "legal": 3,
            "marketing": 2,
            "default": 1
        }
        
        # Subscribe to context update events
        event_bus.subscribe("shared_context_updated", self._handle_context_update)
    
    async def store_shared_context(self, 
                                 context_type: str, 
                                 content: Dict[str, Any],
                                 source_agent: str,
                                 access_control: Optional[Dict[str, Any]] = None,
                                 parent_version_id: Optional[str] = None,
                                 change_description: Optional[str] = None,
                                 confidence: float = 1.0) -> str:
        """Store context that should be accessible to multiple agents"""
        # Generate context ID if this is a new context
        context_id = f"{context_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate version ID
        version_id = f"{context_id}_v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create version object
        version = ContextVersion(
            version_id=version_id,
            content=content,
            created_by=source_agent,
            parent_version_id=parent_version_id,
            change_description=change_description
        )
        
        # Store version
        if context_id not in self.context_versions:
            self.context_versions[context_id] = []
        
        self.context_versions[context_id].append(version)
        
        # Set up access control
        if context_id not in self.access_controls:
            # Default access control if not specified
            if not access_control:
                access_control = {
                    "read_roles": ["cofounder", "manager", "strategy", "finance", "legal", "marketing"],
                    "write_roles": [source_agent.lower()],
                    "owner": source_agent
                }
            
            self.access_controls[context_id] = AccessControl(
                read_roles=set(access_control.get("read_roles", [])),
                write_roles=set(access_control.get("write_roles", [])),
                owner=access_control.get("owner", source_agent)
            )
        
        # Store in memory manager
        metadata = {
            "context_id": context_id,
            "version_id": version_id,
            "access_control": self.access_controls[context_id].dict()
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=source_agent,
            memory_type=f"shared_context_{context_type}",
            content=content,
            metadata=metadata,
            is_shared=True,
            confidence=confidence
        )
        
        # Publish context update event
        await event_bus.publish("shared_context_updated", {
            "context_id": context_id,
            "version_id": version_id,
            "context_type": context_type,
            "source_agent": source_agent,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Stored shared context {context_id} version {version_id} from {source_agent}")
        return context_id
    
    async def get_shared_context(self, 
                               context_type: Optional[str] = None,
                               query: Optional[str] = None,
                               requesting_agent: Optional[str] = None,
                               version_id: Optional[str] = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Get shared context accessible to the requesting agent"""
        # Determine agent role
        agent_role = requesting_agent.lower() if requesting_agent else "default"
        
        # Get all shared contexts from memory manager
        filter_type = f"shared_context_{context_type}" if context_type else None
        
        if query and not version_id:
            # Use semantic search for query
            search_results = await self.memory_manager.semantic_search(
                query=query,
                memory_type=filter_type,
                limit=limit * 2  # Get more results for filtering
            )
            
            # Extract contexts from search results
            contexts = []
            for result in search_results:
                context_data = result.get("content", {})
                metadata = result.get("metadata", {})
                
                # Check access control
                context_id = metadata.get("context_id")
                if context_id and self._check_read_access(context_id, agent_role):
                    contexts.append({
                        "context_id": context_id,
                        "version_id": metadata.get("version_id"),
                        "content": context_data,
                        "created_by": metadata.get("agent"),
                        "created_at": metadata.get("timestamp"),
                        "relevance_score": result.get("score", 0)
                    })
            
            return contexts[:limit]
        else:
            # Direct retrieval by type or version
            shared_memories = await self.memory_manager.query_agent_memory(
                agent_name="*",  # All agents
                memory_type=filter_type,
                include_shared=True
            )
            
            # Filter by access control and version if specified
            contexts = []
            for memory in shared_memories:
                metadata = memory.get("metadata", {})
                context_id = metadata.get("context_id")
                
                # Skip if no context_id or no read access
                if not context_id or not self._check_read_access(context_id, agent_role):
                    continue
                
                # Filter by version_id if specified
                if version_id and metadata.get("version_id") != version_id:
                    continue
                
                contexts.append({
                    "context_id": context_id,
                    "version_id": metadata.get("version_id"),
                    "content": memory.get("content", {}),
                    "created_by": memory.get("author"),
                    "created_at": memory.get("timestamp")
                })
            
            # Sort by timestamp (newest first) and limit
            contexts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return contexts[:limit]
    
    async def update_shared_context(self,
                                  context_id: str,
                                  updates: Dict[str, Any],
                                  updating_agent: str,
                                  change_description: Optional[str] = None) -> Dict[str, Any]:
        """Update existing shared context with versioning"""
        # Check write access
        agent_role = updating_agent.lower()
        if not self._check_write_access(context_id, agent_role):
            error_msg = f"Agent {updating_agent} does not have write access to context {context_id}"
            logger.warning(error_msg)
            return {"error": "access_denied", "message": error_msg}
        
        # Get latest version
        latest_version = self._get_latest_version(context_id)
        if not latest_version:
            error_msg = f"Context {context_id} not found"
            logger.warning(error_msg)
            return {"error": "not_found", "message": error_msg}
        
        # Create new content by merging updates with existing content
        new_content = {**latest_version.content, **updates}
        
        # Extract context type from context_id
        context_type = context_id.split("_")[0] if "_" in context_id else "general"
        
        # Store new version
        await self.store_shared_context(
            context_type=context_type,
            content=new_content,
            source_agent=updating_agent,
            parent_version_id=latest_version.version_id,
            change_description=change_description,
            confidence=1.0  # Assuming high confidence for explicit updates
        )
        
        return {
            "success": True,
            "context_id": context_id,
            "updated_by": updating_agent,
            "updated_at": datetime.now().isoformat()
        }
    
    async def get_context_history(self,
                                context_id: str,
                                requesting_agent: str,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """Get version history for a specific context"""
        # Check read access
        agent_role = requesting_agent.lower()
        if not self._check_read_access(context_id, agent_role):
            logger.warning(f"Agent {requesting_agent} does not have read access to context {context_id}")
            return []
        
        # Get versions
        versions = self.context_versions.get(context_id, [])
        
        # Sort by timestamp (newest first) and limit
        versions.sort(key=lambda v: v.created_at, reverse=True)
        limited_versions = versions[:limit]
        
        # Convert to dict for response
        return [
            {
                "version_id": v.version_id,
                "created_by": v.created_by,
                "created_at": v.created_at,
                "parent_version_id": v.parent_version_id,
                "change_description": v.change_description
            }
            for v in limited_versions
        ]
    
    async def get_agent_specific_context(self,
                                       agent_name: str,
                                       context_type: Optional[str] = None,
                                       query: Optional[str] = None) -> Dict[str, Any]:
        """Get context specific to an agent, including relevant shared context"""
        # Get agent's role
        agent_role = agent_name.lower()
        
        # Get shared context accessible to this agent
        shared_contexts = await self.get_shared_context(
            context_type=context_type,
            query=query,
            requesting_agent=agent_name,
            limit=5
        )
        
        # Get agent's private memory
        private_memories = await self.memory_manager.query_agent_memory(
            agent_name=agent_name,
            memory_type=context_type,
            include_shared=False
        )
        
        # Combine and organize by type
        context_by_type = {}
        
        # Add shared contexts
        for context in shared_contexts:
            content = context.get("content", {})
            ctx_type = context_type or "general"
            
            if ctx_type not in context_by_type:
                context_by_type[ctx_type] = []
                
            context_by_type[ctx_type].append({
                "source": "shared",
                "content": content,
                "created_by": context.get("created_by"),
                "created_at": context.get("created_at"),
                "context_id": context.get("context_id")
            })
        
        # Add private memories
        for memory in private_memories:
            mem_type = memory.get("type", "general")
            
            if mem_type not in context_by_type:
                context_by_type[mem_type] = []
                
            context_by_type[mem_type].append({
                "source": "private",
                "content": memory.get("content", {}),
                "created_at": memory.get("timestamp")
            })
        
        return {
            "agent_name": agent_name,
            "contexts": context_by_type
        }
    
    async def grant_access(self,
                         context_id: str,
                         granting_agent: str,
                         target_role: str,
                         access_type: str) -> Dict[str, Any]:
        """Grant read or write access to a role for a specific context"""
        # Check if granting agent is the owner
        if context_id not in self.access_controls:
            return {"error": "not_found", "message": f"Context {context_id} not found"}
        
        access_control = self.access_controls[context_id]
        if access_control.owner != granting_agent:
            return {"error": "access_denied", "message": "Only the owner can modify access controls"}
        
        # Grant access
        if access_type == "read":
            access_control.read_roles.add(target_role.lower())
        elif access_type == "write":
            access_control.write_roles.add(target_role.lower())
        else:
            return {"error": "invalid_access_type", "message": "Access type must be 'read' or 'write'"}
        
        # Update access control
        self.access_controls[context_id] = access_control
        
        # Log the change
        logger.info(f"{granting_agent} granted {access_type} access to {target_role} for context {context_id}")
        
        return {
            "success": True,
            "context_id": context_id,
            "access_type": access_type,
            "target_role": target_role,
            "granted_by": granting_agent
        }
    
    async def revoke_access(self,
                          context_id: str,
                          revoking_agent: str,
                          target_role: str,
                          access_type: str) -> Dict[str, Any]:
        """Revoke read or write access from a role for a specific context"""
        # Check if revoking agent is the owner
        if context_id not in self.access_controls:
            return {"error": "not_found", "message": f"Context {context_id} not found"}
        
        access_control = self.access_controls[context_id]
        if access_control.owner != revoking_agent:
            return {"error": "access_denied", "message": "Only the owner can modify access controls"}
        
        # Revoke access
        if access_type == "read":
            if target_role.lower() in access_control.read_roles:
                access_control.read_roles.remove(target_role.lower())
        elif access_type == "write":
            if target_role.lower() in access_control.write_roles:
                access_control.write_roles.remove(target_role.lower())
        else:
            return {"error": "invalid_access_type", "message": "Access type must be 'read' or 'write'"}
        
        # Update access control
        self.access_controls[context_id] = access_control
        
        # Log the change
        logger.info(f"{revoking_agent} revoked {access_type} access from {target_role} for context {context_id}")
        
        return {
            "success": True,
            "context_id": context_id,
            "access_type": access_type,
            "target_role": target_role,
            "revoked_by": revoking_agent
        }
    
    async def _handle_context_update(self, event_data: Dict[str, Any]):
        """Handle context update events"""
        context_id = event_data.get("context_id")
        context_type = event_data.get("context_type")
        
        if context_id and context_type:
            # Invalidate cache for this context type
            cache_key = f"shared_context:{context_type}"
            await self.event_cache_manager.invalidate_cache(cache_key)
            
            logger.debug(f"Invalidated cache for {cache_key} due to update")
    
    def _check_read_access(self, context_id: str, agent_role: str) -> bool:
        """Check if an agent role has read access to a context"""
        if context_id not in self.access_controls:
            return False
        
        access_control = self.access_controls[context_id]
        
        # Owner always has access
        if access_control.owner.lower() == agent_role:
            return True
        
        # Check role hierarchy
        agent_level = self.role_hierarchy.get(agent_role, self.role_hierarchy["default"])
        
        # Check direct role access
        if agent_role in access_control.read_roles:
            return True
        
        # Check if any of the agent's roles have access
        for role in access_control.read_roles:
            role_level = self.role_hierarchy.get(role, self.role_hierarchy["default"])
            if agent_level >= role_level:
                return True
        
        return False
    
    def _check_write_access(self, context_id: str, agent_role: str) -> bool:
        """Check if an agent role has write access to a context"""
        if context_id not in self.access_controls:
            return False
        
        access_control = self.access_controls[context_id]
        
        # Owner always has access
        if access_control.owner.lower() == agent_role:
            return True
        
        # Check direct role access
        if agent_role in access_control.write_roles:
            return True
        
        # For write access, we don't use role hierarchy - must be explicitly granted
        return False
    
    def _get_latest_version(self, context_id: str) -> Optional[ContextVersion]:
        """Get the latest version of a context"""
        if context_id not in self.context_versions or not self.context_versions[context_id]:
            return None
        
        # Sort by timestamp (newest first)
        versions = sorted(self.context_versions[context_id], key=lambda v: v.created_at, reverse=True)
        return versions[0] if versions else None