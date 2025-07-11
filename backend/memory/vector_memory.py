from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScalarQuantization, HnswConfigDiff, QuantizationConfig
from typing import List, Dict, Any, Optional, Union
import asyncio
import os
import hashlib
import google.generativeai as genai
from loguru import logger

class VectorMemory:
    """Qdrant-based semantic memory for RAG operations"""
    
    def __init__(self):
        # Debug logging
        logger.debug(f"Environment variables loaded from: {os.path.abspath('../.env')}")        
        self.url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")
        logger.debug(f"QDRANT_URL: {self.url}")
        logger.debug(f"QDRANT_API_KEY: {'set' if self.api_key else 'not set'}")
        if not self.url or not self.api_key:
            raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in .env")
        # Remove any trailing slashes from the URL
        self.url = self.url.rstrip('/')
        # For cloud URLs, ensure we're using https://
        if not self.url.startswith('http'):
            self.url = f"https://{self.url}"
        self.client = QdrantClient(url=self.url, api_key=self.api_key, timeout=60)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.embedding_model = "models/embedding-001"
        self.collection_name = "agentflow_memory"
        self._setup_collection()
    
    def _setup_collection(self):
        """Initialize Qdrant collection with optimized HNSW indexing and scalar quantization"""
        try:
            collections = self.client.get_collections().collections
            if not any(col.name == self.collection_name for col in collections):
                # Create collection with optimized parameters
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768, 
                        distance=Distance.COSINE,
                        # HNSW configuration for better performance
                        hnsw_config=HnswConfigDiff(
                            m=16,  # Number of bidirectional links created for each new element
                            ef_construct=128,  # Size of the dynamic candidate list for constructing the graph
                        ),
                        # Scalar quantization for memory efficiency
                        quantization_config=QuantizationConfig(
                            scalar=ScalarQuantization(
                                type="int8",  # 8-bit quantization for memory efficiency
                                always_ram=True  # Keep quantized vectors in RAM
                            )
                        )
                    )
                )
                logger.info(f"Created Qdrant collection with optimized HNSW indexing: {self.collection_name}")
            else:
                # Update existing collection with optimized parameters
                self.client.update_collection(
                    collection_name=self.collection_name,
                    optimizer_config={
                        "indexing_threshold": 10000,  # Start indexing after 10k vectors
                        "memmap_threshold": 50000,  # Use memmap after 50k vectors
                    },
                    hnsw_config={
                        "m": 16,
                        "ef_construct": 128,
                    }
                )
                logger.info(f"Updated Qdrant collection with optimized parameters: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to setup Qdrant collection: {e}")
    
    def _generate_id(self, text: str, agent: str) -> str:
        """Generate unique ID for document"""
        import uuid
        # Generate deterministic UUID from content
        content_hash = f"{agent}_{text[:100]}_{len(text)}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, content_hash))
    
    async def store_document(self, text: str, metadata: Dict[str, Any], agent: str) -> str:
        """Store document with semantic embedding"""
        try:
            # Generate embedding
            embedding = genai.embed_content(model=self.embedding_model, content=text, task_type="retrieval_document")["embedding"]
            
            # Create point
            point_id = self._generate_id(text, agent)
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": text,
                    "agent": agent,
                    "timestamp": metadata.get("timestamp"),
                    "type": metadata.get("type", "document"),
                    **metadata
                }
            )
            
            # Store in Qdrant with optimized parameters
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
                wait=False  # Async operation for better performance
            )
            
            logger.info(f"Stored document for agent {agent}")
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise
    
    async def semantic_search(self, query: str, agent: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        try:
            # Generate query embedding
            query_embedding = genai.embed_content(model=self.embedding_model, content=query, task_type="retrieval_query")["embedding"]
            
            # Build filter
            filter_conditions = None
            if agent:
                filter_conditions = {"must": [{"key": "agent", "match": {"value": agent}}]}
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload["text"],
                    "agent": result.payload["agent"],
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["text", "agent"]}
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def get_agent_documents(self, agent: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all documents for a specific agent"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "agent", "match": {"value": agent}}]},
                limit=limit,
                with_payload=True
            )
            
            documents = []
            for point in results[0]:
                documents.append({
                    "id": point.id,
                    "text": point.payload["text"],
                    "metadata": {k: v for k, v in point.payload.items() 
                               if k not in ["text", "agent"]}
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get agent documents: {e}")
            return []
    
    async def delete_agent_documents(self, agent: str) -> bool:
        """Delete all documents for an agent"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={"filter": {"must": [{"key": "agent", "match": {"value": agent}}]}}
            )
            logger.info(f"Deleted documents for agent {agent}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent documents: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information and statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            # Get additional telemetry for performance monitoring
            telemetry = self.client.get_collection_cluster_info(self.collection_name)
            
            return {
                "vectors_count": collection_info.vectors_count,
                "status": "ready",
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "optimization_enabled": collection_info.optimizer_status.enabled if collection_info.optimizer_status else False,
                "cluster_info": {
                    "peer_count": len(telemetry.peer_id) if telemetry else 0,
                    "shard_count": len(telemetry.shard_count) if telemetry else 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"vectors_count": 0, "status": "error"}
    
    async def clear_collection(self):
        """Clear all documents from collection"""
        try:
            # More efficient than deleting and recreating the collection
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=None,  # Delete all points
                wait=True  # Wait for operation to complete
            )
            logger.info("Cleared vector memory collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            # Fallback to recreating the collection if delete fails
            try:
                self.client.delete_collection(self.collection_name)
                self._setup_collection()
                logger.info("Recreated vector memory collection")
            except Exception as e2:
                logger.error(f"Failed to recreate collection: {e2}")
    
    async def add_document(self, text: str, metadata: Dict[str, Any], doc_id: str):
        """Add document with specific ID"""
        try:
            embedding = genai.embed_content(model=self.embedding_model, content=text, task_type="retrieval_document")["embedding"]
            
            # Generate valid UUID from doc_id if it's not already valid
            import uuid
            try:
                # Try to use as UUID
                point_id = str(uuid.UUID(doc_id))
            except ValueError:
                # Generate UUID from string hash
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={"text": text, "original_id": doc_id, **metadata}
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
                wait=False  # Async operation for better performance
            )
            
            logger.info(f"Added document with ID: {point_id} (original: {doc_id})")
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def search(self, query: str, limit: int = 5, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search with optional filters and optimized parameters"""
        try:
            query_embedding = genai.embed_content(model=self.embedding_model, content=query, task_type="retrieval_query")["embedding"]
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                with_payload=True,
                # Optimized search parameters
                search_params={
                    "hnsw_ef": 128,  # Higher ef value for better recall
                    "exact": False   # Use approximate search for speed
                },
                score_threshold=0.7  # Only return results with similarity above threshold
            )
            
            return [{
                "text": result.payload["text"],
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            } for result in results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def batch_add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add multiple documents in a batch for better performance"""
        try:
            if not documents:
                return []
                
            # Process embeddings in parallel with asyncio
            async def process_document(doc):
                text = doc["text"]
                metadata = doc["metadata"]
                doc_id = doc.get("id", self._generate_id(text, metadata.get("agent", "system")))
                
                embedding = genai.embed_content(
                    model=self.embedding_model, 
                    content=text, 
                    task_type="retrieval_document"
                )["embedding"]
                
                return PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={"text": text, **metadata}
                ), doc_id
            
            # Process in batches of 10 to avoid rate limiting
            batch_size = 10
            all_ids = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                points_with_ids = await asyncio.gather(*[process_document(doc) for doc in batch])
                
                points = [p[0] for p in points_with_ids]
                ids = [p[1] for p in points_with_ids]
                
                # Upsert batch
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=False
                )
                
                all_ids.extend(ids)
                
                # Small delay between batches
                if i + batch_size < len(documents):
                    await asyncio.sleep(0.5)
            
            logger.info(f"Batch added {len(all_ids)} documents to vector memory")
            return all_ids
            
        except Exception as e:
            logger.error(f"Batch document add failed: {e}")
            raise