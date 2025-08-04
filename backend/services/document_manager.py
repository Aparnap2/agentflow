"""
Document Manager Service - Handles document storage, retrieval, and metadata
"""
import os
import json
import shutil
from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
from datetime import datetime
from loguru import logger
import uuid

from database.neo4j_client import Neo4jClient
from services.template_manager import template_manager
from services.document_converter import document_converter

class DocumentManager:
    """Manages document storage, retrieval, and metadata"""
    
    def __init__(self):
        # Set up document directory
        self.document_dir = Path("./data/documents")
        self.document_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize Neo4j client for document metadata
        self.neo4j_client = Neo4jClient()
        
        # Create document schema in Neo4j
        self._create_document_schema()
    
    def _create_document_schema(self):
        """Create document schema in Neo4j"""
        try:
            # Create constraints for documents
            query = """
            CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
            """
            self.neo4j_client.execute_query(query)
            
            logger.info("Document schema created in Neo4j")
        except Exception as e:
            logger.error(f"Failed to create document schema: {e}")
    
    async def generate_document(self, 
                         agent_type: str, 
                         template_name: str, 
                         data: Dict[str, Any],
                         output_format: str = "pdf",
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a document using a template and data"""
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Merge metadata
            metadata = metadata or {}
            metadata["agent_type"] = agent_type
            metadata["template_name"] = template_name
            metadata["document_id"] = document_id
            
            # Add filename if not provided
            if "filename" not in metadata:
                metadata["filename"] = f"{agent_type}_{template_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Render template
            content = template_manager.render_template(agent_type, template_name, data)
            
            # Convert to desired format
            result = document_converter.convert(
                content=content,
                source_format="md",  # Assuming templates are in markdown
                target_format=output_format,
                metadata=metadata
            )
            
            # Check for errors
            if "error" in result:
                return result
            
            # Store document metadata in Neo4j
            self._store_document_metadata(document_id, result["path"], output_format, metadata)
            
            # Return document info
            return {
                "document_id": document_id,
                "path": result["path"],
                "format": output_format,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to generate document: {e}")
            return {"error": f"Failed to generate document: {str(e)}"}
    
    def _store_document_metadata(self, document_id: str, path: str, format: str, metadata: Dict[str, Any]):
        """Store document metadata in Neo4j"""
        try:
            # Create query to store document metadata
            query = """
            CREATE (d:Document {id: $id})
            SET d.path = $path,
                d.format = $format,
                d.agent_type = $agent_type,
                d.template_name = $template_name,
                d.title = $title,
                d.created_at = $created_at,
                d.metadata = $metadata
            RETURN d
            """
            
            params = {
                "id": document_id,
                "path": path,
                "format": format,
                "agent_type": metadata.get("agent_type", "unknown"),
                "template_name": metadata.get("template_name", "unknown"),
                "title": metadata.get("title", "Untitled Document"),
                "created_at": datetime.now().isoformat(),
                "metadata": json.dumps(metadata)
            }
            
            # Execute query
            self.neo4j_client.execute_query(query, params)
            
            logger.info(f"Stored document metadata for {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document by ID"""
        try:
            # Query document metadata
            query = """
            MATCH (d:Document {id: $id})
            RETURN d.id as id, d.path as path, d.format as format, 
                   d.agent_type as agent_type, d.template_name as template_name,
                   d.title as title, d.created_at as created_at, d.metadata as metadata
            """
            
            params = {"id": document_id}
            
            results = self.neo4j_client.execute_query(query, params)
            
            if not results:
                return {"error": f"Document not found: {document_id}"}
            
            document = results[0]
            
            # Check if file exists
            file_path = document["path"]
            if not os.path.exists(file_path):
                return {"error": f"Document file not found: {file_path}"}
            
            # Parse metadata
            try:
                metadata = json.loads(document["metadata"])
            except:
                metadata = {}
            
            return {
                "document_id": document["id"],
                "path": document["path"],
                "format": document["format"],
                "agent_type": document["agent_type"],
                "template_name": document["template_name"],
                "title": document["title"],
                "created_at": document["created_at"],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return {"error": f"Failed to get document: {str(e)}"}
    
    def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get document content by ID"""
        try:
            # Get document metadata
            document = self.get_document(document_id)
            
            if "error" in document:
                return document
            
            # Read file content
            with open(document["path"], "rb") as f:
                content = f.read()
            
            return {
                "document_id": document["document_id"],
                "format": document["format"],
                "content": content,
                "metadata": document["metadata"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get document content {document_id}: {e}")
            return {"error": f"Failed to get document content: {str(e)}"}
    
    def list_documents(self, 
                      agent_type: Optional[str] = None, 
                      format: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """List documents, optionally filtered by agent type and format"""
        try:
            # Build query based on filters
            if agent_type and format:
                query = """
                MATCH (d:Document)
                WHERE d.agent_type = $agent_type AND d.format = $format
                RETURN d.id as id, d.path as path, d.format as format, 
                       d.agent_type as agent_type, d.template_name as template_name,
                       d.title as title, d.created_at as created_at
                ORDER BY d.created_at DESC
                LIMIT $limit
                """
                params = {"agent_type": agent_type, "format": format, "limit": limit}
            elif agent_type:
                query = """
                MATCH (d:Document)
                WHERE d.agent_type = $agent_type
                RETURN d.id as id, d.path as path, d.format as format, 
                       d.agent_type as agent_type, d.template_name as template_name,
                       d.title as title, d.created_at as created_at
                ORDER BY d.created_at DESC
                LIMIT $limit
                """
                params = {"agent_type": agent_type, "limit": limit}
            elif format:
                query = """
                MATCH (d:Document)
                WHERE d.format = $format
                RETURN d.id as id, d.path as path, d.format as format, 
                       d.agent_type as agent_type, d.template_name as template_name,
                       d.title as title, d.created_at as created_at
                ORDER BY d.created_at DESC
                LIMIT $limit
                """
                params = {"format": format, "limit": limit}
            else:
                query = """
                MATCH (d:Document)
                RETURN d.id as id, d.path as path, d.format as format, 
                       d.agent_type as agent_type, d.template_name as template_name,
                       d.title as title, d.created_at as created_at
                ORDER BY d.created_at DESC
                LIMIT $limit
                """
                params = {"limit": limit}
            
            results = self.neo4j_client.execute_query(query, params)
            
            # Format results
            documents = []
            for doc in results:
                documents.append({
                    "document_id": doc["id"],
                    "path": doc["path"],
                    "format": doc["format"],
                    "agent_type": doc["agent_type"],
                    "template_name": doc["template_name"],
                    "title": doc["title"],
                    "created_at": doc["created_at"]
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            # Get document metadata
            document = self.get_document(document_id)
            
            if "error" in document:
                return False
            
            # Delete file
            file_path = document["path"]
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete metadata from Neo4j
            query = """
            MATCH (d:Document {id: $id})
            DELETE d
            """
            
            params = {"id": document_id}
            
            self.neo4j_client.execute_query(query, params)
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def search_documents(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search documents by title or content"""
        try:
            # Search by title (simple text search)
            cypher_query = """
            MATCH (d:Document)
            WHERE d.title CONTAINS $query
            RETURN d.id as id, d.path as path, d.format as format, 
                   d.agent_type as agent_type, d.template_name as template_name,
                   d.title as title, d.created_at as created_at
            ORDER BY d.created_at DESC
            LIMIT $limit
            """
            
            params = {"query": query, "limit": limit}
            
            results = self.neo4j_client.execute_query(cypher_query, params)
            
            # Format results
            documents = []
            for doc in results:
                documents.append({
                    "document_id": doc["id"],
                    "path": doc["path"],
                    "format": doc["format"],
                    "agent_type": doc["agent_type"],
                    "template_name": doc["template_name"],
                    "title": doc["title"],
                    "created_at": doc["created_at"],
                    "match_type": "title"
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

# Global instance
document_manager = DocumentManager()