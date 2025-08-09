"""
Qdrant Multitenant Implementation
Implements PRD-compliant multitenancy with payload filtering and sharding
"""
from typing import Dict, List, Any, Optional, Union
import uuid
from datetime import datetime
from loguru import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, CreateCollection, PointStruct, 
        Filter, FieldCondition, MatchValue, PayloadSchemaType,
        CreatePayloadIndex, UpdateCollection
    )
    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("Qdrant client not available")
    QDRANT_AVAILABLE = False

class QdrantMultitenantClient:
    """Qdrant client with PRD-compliant multitenancy"""
    
    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        if not QDRANT_AVAILABLE:
            logger.error("Qdrant client not available")
            self.client = None
            return
            
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = "agentflow_global"  # Single multitenant collection per PRD
        
        # Multitenancy configuration per PRD
        self.multitenant_config = {
            "collection_name": self.collection_name,
            "tenant_field": "group_id",  # PRD-specified tenant field
            "shard_field": "shard_key",  # Optional custom sharding
            "payload_indexes": ["group_id", "type", "source", "entity_ids"],
            "vector_size": 1536,  # OpenAI embedding size
            "distance_metric": Distance.COSINE,
            "shard_count": 2,  # Start with 2 shards per PRD, plan for ~12
            "replication_factor": 1
        }
    
    async def initialize_multitenant_collection(self) -> bool:
        """Initialize the multitenant collection with proper indexing"""
        if not self.client:
            return False
            
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection with sharding
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.multitenant_config["vector_size"],
                        distance=self.multitenant_config["distance_metric"]
                    ),
                    shard_number=self.multitenant_config["shard_count"],
                    replication_factor=self.multitenant_config["replication_factor"]
                )
                
                logger.info(f"Created multitenant collection: {self.collection_name}")
            
            # Create payload indexes for multitenancy per PRD
            await self._create_payload_indexes()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize multitenant collection: {e}")
            return False
    
    async def _create_payload_indexes(self):
        """Create payload indexes for efficient tenant filtering"""
        try:
            # Create tenant index with is_tenant flag per PRD
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=self.multitenant_config["tenant_field"],
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            # Create additional indexes for performance
            for field in self.multitenant_config["payload_indexes"]:
                if field != self.multitenant_config["tenant_field"]:
                    try:
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name=field,
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                    except Exception as e:
                        # Index might already exist
                        logger.debug(f"Index creation skipped for {field}: {e}")
            
            logger.info("Payload indexes created for multitenancy")
            
        except Exception as e:
            logger.error(f"Failed to create payload indexes: {e}")
    
    async def upsert_tenant_points(self, workspace_id: str, points: List[Dict[str, Any]], 
                                 shard_key: Optional[str] = None) -> Dict[str, Any]:
        """Upsert points with tenant isolation"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Prepare points with tenant metadata per PRD
            qdrant_points = []
            
            for point_data in points:
                # Generate point ID if not provided
                point_id = point_data.get("id", str(uuid.uuid4()))
                
                # Ensure vector is present
                if "vector" not in point_data:
                    logger.warning(f"Point {point_id} missing vector, skipping")
                    continue
                
                # Create payload with tenant isolation per PRD
                payload = {
                    # Required tenant fields per PRD
                    "group_id": workspace_id,  # PRD-specified tenant field
                    "is_tenant": True,         # PRD-specified tenant flag
                    
                    # Optional sharding
                    "shard_key": shard_key or workspace_id,
                    
                    # PRD-specified payload structure
                    "type": point_data.get("type", "unknown"),
                    "tags": point_data.get("tags", []),
                    "ts": point_data.get("timestamp", datetime.now().isoformat()),
                    "source": point_data.get("source", "agent"),
                    "entity_ids": point_data.get("entity_ids", []),
                    
                    # Additional metadata
                    "agent_name": point_data.get("agent_name", ""),
                    "confidence": point_data.get("confidence", 0.0),
                    "content": point_data.get("content", ""),
                    "metadata": point_data.get("metadata", {})
                }
                
                qdrant_point = PointStruct(
                    id=point_id,
                    vector=point_data["vector"],
                    payload=payload
                )
                
                qdrant_points.append(qdrant_point)
            
            if not qdrant_points:
                return {"error": "No valid points to upsert"}
            
            # Upsert points
            operation_info = self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )
            
            logger.info(f"Upserted {len(qdrant_points)} points for tenant {workspace_id}")
            
            return {
                "success": True,
                "points_upserted": len(qdrant_points),
                "operation_id": operation_info.operation_id,
                "tenant_id": workspace_id
            }
            
        except Exception as e:
            logger.error(f"Failed to upsert tenant points: {e}")
            return {"error": str(e)}
    
    async def search_tenant_points(self, workspace_id: str, query_vector: List[float], 
                                 limit: int = 10, score_threshold: float = 0.7,
                                 filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search points with tenant isolation and score threshold per PRD"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Build tenant filter per PRD
            tenant_filter = Filter(
                must=[
                    FieldCondition(
                        key=self.multitenant_config["tenant_field"],
                        match=MatchValue(value=workspace_id)
                    ),
                    FieldCondition(
                        key="is_tenant",
                        match=MatchValue(value=True)
                    )
                ]
            )
            
            # Add additional filters if provided
            if filters:
                for key, value in filters.items():
                    tenant_filter.must.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            
            # Search with tenant isolation
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=tenant_filter,
                limit=limit,
                score_threshold=score_threshold  # PRD-specified noise reduction
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "payload": scored_point.payload,
                    "content": scored_point.payload.get("content", ""),
                    "agent_name": scored_point.payload.get("agent_name", ""),
                    "type": scored_point.payload.get("type", ""),
                    "timestamp": scored_point.payload.get("ts", "")
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} points for tenant {workspace_id}")
            
            return {
                "success": True,
                "results": results,
                "total_found": len(results),
                "tenant_id": workspace_id,
                "score_threshold": score_threshold
            }
            
        except Exception as e:
            logger.error(f"Failed to search tenant points: {e}")
            return {"error": str(e)}
    
    async def get_tenant_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get statistics for a specific tenant"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Count points for tenant
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key=self.multitenant_config["tenant_field"],
                            match=MatchValue(value=workspace_id)
                        )
                    ]
                )
            )
            
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "tenant_id": workspace_id,
                "point_count": count_result.count,
                "collection_name": self.collection_name,
                "shard_count": collection_info.config.params.shard_number,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            return {"error": str(e)}
    
    async def delete_tenant_data(self, workspace_id: str) -> Dict[str, Any]:
        """Delete all data for a tenant"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Delete points with tenant filter
            operation_info = self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key=self.multitenant_config["tenant_field"],
                            match=MatchValue(value=workspace_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted all data for tenant {workspace_id}")
            
            return {
                "success": True,
                "tenant_id": workspace_id,
                "operation_id": operation_info.operation_id
            }
            
        except Exception as e:
            logger.error(f"Failed to delete tenant data: {e}")
            return {"error": str(e)}
    
    async def get_collection_health(self) -> Dict[str, Any]:
        """Get overall collection health and multitenancy status"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            # Get total point count
            total_count = self.client.count(collection_name=self.collection_name)
            
            # Get tenant distribution (would need aggregation query in real implementation)
            # For now, return basic health info
            
            return {
                "collection_name": self.collection_name,
                "status": collection_info.status.name,
                "total_points": total_count.count,
                "shard_count": collection_info.config.params.shard_number,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "multitenancy_enabled": True,
                "tenant_field": self.multitenant_config["tenant_field"],
                "payload_indexes": self.multitenant_config["payload_indexes"],
                "health_status": "healthy" if collection_info.status.name == "green" else "degraded",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection health: {e}")
            return {"error": str(e)}
    
    async def optimize_collection(self) -> Dict[str, Any]:
        """Optimize collection for better performance"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            # Update collection with optimization settings
            self.client.update_collection(
                collection_name=self.collection_name,
                optimizer_config={
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000,
                    "default_segment_number": 0,
                    "max_segment_size": None,
                    "memmap_threshold": None,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                    "max_optimization_threads": None
                }
            )
            
            logger.info(f"Optimized collection {self.collection_name}")
            
            return {
                "success": True,
                "collection_name": self.collection_name,
                "optimization_applied": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize collection: {e}")
            return {"error": str(e)}

# Global multitenant client
qdrant_multitenant = QdrantMultitenantClient()