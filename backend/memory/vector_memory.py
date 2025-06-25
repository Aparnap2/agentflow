from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import os
import hashlib
from sentence_transformers import SentenceTransformer
from loguru import logger

class VectorMemory:
    """Qdrant-based semantic memory for RAG operations"""
    
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "agentflow_memory"
        self._setup_collection()
    
    def _setup_collection(self):
        """Initialize Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            if not any(col.name == self.collection_name for col in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to setup Qdrant collection: {e}")
    
    def _generate_id(self, text: str, agent: str) -> str:
        """Generate unique ID for document"""
        return hashlib.md5(f"{agent}:{text}".encode()).hexdigest()
    
    async def store_document(self, text: str, metadata: Dict[str, Any], agent: str) -> str:
        """Store document with semantic embedding"""
        try:
            # Generate embedding
            embedding = self.encoder.encode(text).tolist()
            
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
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
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
            query_embedding = self.encoder.encode(query).tolist()
            
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