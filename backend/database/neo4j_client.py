"""
Neo4j Client - Handles connections and queries to Neo4j database
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase, AsyncGraphDatabase
from loguru import logger

class Neo4jClient:
    """Client for Neo4j database operations"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self.async_driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.async_driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self._create_constraints()
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.warning(f"Neo4j connection failed, using fallback: {e}")
            self.driver = None
            self.async_driver = None
    
    def _create_constraints(self):
        """Create necessary constraints and indexes"""
        if not self.driver:
            return
            
        constraints = [
            "CREATE CONSTRAINT template_name IF NOT EXISTS FOR (t:Template) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint creation issue (may already exist): {e}")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Neo4j query synchronously"""
        if not self.driver:
            logger.warning("Neo4j driver not available, using fallback mode")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            raise
    
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Neo4j query asynchronously"""
        if not self.async_driver:
            logger.warning("Neo4j async driver not available, using fallback mode")
            return []
        
        try:
            async with self.async_driver.session() as session:
                result = await session.run(query, parameters or {})
                records = await result.values()
                return [dict(zip(result.keys(), record)) for record in records]
        except Exception as e:
            logger.error(f"Neo4j async query failed: {e}")
            raise
    
    async def store_template(self, name: str, content: str, agent_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a template in Neo4j"""
        query = """
        MERGE (t:Template {name: $name})
        SET t.content = $content,
            t.agent_type = $agent_type,
            t.metadata = $metadata,
            t.updated_at = datetime()
        RETURN t.name as name
        """
        
        result = await self.execute_query(
            query,
            {
                "name": name,
                "content": content,
                "agent_type": agent_type,
                "metadata": json.dumps(metadata or {})
            }
        )
        
        return result[0]["name"] if result else name
    
    async def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template from Neo4j"""
        query = """
        MATCH (t:Template {name: $name})
        RETURN t.content as content,
               t.agent_type as agent_type,
               t.metadata as metadata,
               t.updated_at as updated_at
        """
        
        result = await self.execute_query(query, {"name": name})
        
        if not result:
            return None
            
        template_data = result[0]
        return {
            "name": name,
            "content": template_data["content"],
            "agent_type": template_data["agent_type"],
            "metadata": json.loads(template_data["metadata"]),
            "updated_at": template_data["updated_at"]
        }
    
    async def list_templates(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List templates from Neo4j"""
        query = """
        MATCH (t:Template)
        WHERE $agent_type IS NULL OR t.agent_type = $agent_type
        RETURN t.name as name,
               t.agent_type as agent_type,
               t.metadata as metadata,
               t.updated_at as updated_at
        """
        
        results = await self.execute_query(query, {"agent_type": agent_type})
        
        return [{
            "name": result["name"],
            "agent_type": result["agent_type"],
            "metadata": json.loads(result["metadata"]),
            "updated_at": result["updated_at"]
        } for result in results]
    
    async def delete_template(self, name: str) -> bool:
        """Delete a template from Neo4j"""
        query = """
        MATCH (t:Template {name: $name})
        DELETE t
        RETURN count(t) as deleted
        """
        
        result = await self.execute_query(query, {"name": name})
        
        return result[0]["deleted"] > 0 if result else False
    
    async def store_document_metadata(self, document_id: str, path: str, format: str, metadata: Dict[str, Any]) -> bool:
        """Store document metadata in Neo4j"""
        query = """
        MERGE (d:Document {id: $id})
        SET d.path = $path,
            d.format = $format,
            d.metadata = $metadata,
            d.created_at = CASE WHEN d.created_at IS NULL THEN datetime() ELSE d.created_at END,
            d.updated_at = datetime()
        RETURN d.id as id
        """
        
        result = await self.execute_query(
            query,
            {
                "id": document_id,
                "path": path,
                "format": format,
                "metadata": json.dumps(metadata or {})
            }
        )
        
        return bool(result)
    
    async def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata from Neo4j"""
        query = """
        MATCH (d:Document {id: $id})
        RETURN d.path as path,
               d.format as format,
               d.metadata as metadata,
               d.created_at as created_at,
               d.updated_at as updated_at
        """
        
        result = await self.execute_query(query, {"id": document_id})
        
        if not result:
            return None
            
        doc_data = result[0]
        return {
            "id": document_id,
            "path": doc_data["path"],
            "format": doc_data["format"],
            "metadata": json.loads(doc_data["metadata"]),
            "created_at": doc_data["created_at"],
            "updated_at": doc_data["updated_at"]
        }
    
    async def list_documents(self, format: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List documents from Neo4j"""
        query = """
        MATCH (d:Document)
        WHERE $format IS NULL OR d.format = $format
        RETURN d.id as id,
               d.path as path,
               d.format as format,
               d.metadata as metadata,
               d.created_at as created_at,
               d.updated_at as updated_at
        ORDER BY d.updated_at DESC
        LIMIT $limit
        """
        
        results = await self.execute_query(query, {"format": format, "limit": limit})
        
        return [{
            "id": result["id"],
            "path": result["path"],
            "format": result["format"],
            "metadata": json.loads(result["metadata"]),
            "created_at": result["created_at"],
            "updated_at": result["updated_at"]
        } for result in results]
    
    async def delete_document_metadata(self, document_id: str) -> bool:
        """Delete document metadata from Neo4j"""
        query = """
        MATCH (d:Document {id: $id})
        DELETE d
        RETURN count(d) as deleted
        """
        
        result = await self.execute_query(query, {"id": document_id})
        
        return result[0]["deleted"] > 0 if result else False
    
    async def search_documents(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents in Neo4j"""
        query = """
        MATCH (d:Document)
        WHERE d.metadata CONTAINS $query
        RETURN d.id as id,
               d.path as path,
               d.format as format,
               d.metadata as metadata,
               d.created_at as created_at,
               d.updated_at as updated_at
        ORDER BY d.updated_at DESC
        LIMIT $limit
        """
        
        results = await self.execute_query(query, {"query": query_text, "limit": limit})
        
        return [{
            "id": result["id"],
            "path": result["path"],
            "format": result["format"],
            "metadata": json.loads(result["metadata"]),
            "created_at": result["created_at"],
            "updated_at": result["updated_at"]
        } for result in results]
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
        if self.async_driver:
            self.async_driver.close()