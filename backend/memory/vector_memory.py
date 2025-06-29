from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import os
import hashlib
import google.generativeai as genai
from loguru import logger

class VectorMemory:
    """Qdrant-based semantic memory for RAG operations"""
    
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.embedding_model = "models/embedding-001"
        self.collection_name = "agentflow_memory"
        self._setup_collection()
    
    def _setup_collection(self):
        """Initialize Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            if not any(col.name == self.collection_name for col in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to setup Qdrant collection: {e}")
    
    def _generate_id(self, text: str, agent: str) -> str:
        """Generate unique ID for document"""
        import uuid
        return str(uuid.uuid4())
    
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
            return {
                "vectors_count": collection_info.vectors_count,
                "status": "ready",
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"vectors_count": 0, "status": "error"}
    
    async def clear_collection(self):
        """Clear all documents from collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self._setup_collection()
            logger.info("Cleared vector memory collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
    
    async def add_document(self, text: str, metadata: Dict[str, Any], doc_id: str):
        """Add document with specific ID"""
        try:
            embedding = genai.embed_content(model=self.embedding_model, content=text, task_type="retrieval_document")["embedding"]
            
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={"text": text, **metadata}
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added document with ID: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
    
    async def search(self, query: str, limit: int = 5, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search with optional filters"""
        try:
            query_embedding = genai.embed_content(model=self.embedding_model, content=query, task_type="retrieval_query")["embedding"]
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                with_payload=True
            )
            
            return [{
                "text": result.payload["text"],
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            } for result in results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []