from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from loguru import logger

class GraphMemory:
    """Neo4j-based memory system for agent collaboration"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "agentflow123")
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
    
    async def write_private_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any]):
        """Write to agent's private memory"""
        with self.driver.session() as session:
            query = """
            MERGE (a:Agent {name: $agent_name})
            CREATE (m:PrivateMemory {
                type: $memory_type,
                content: $content,
                timestamp: datetime(),
                agent: $agent_name
            })
            CREATE (a)-[:HAS_PRIVATE_MEMORY]->(m)
            RETURN m.timestamp as timestamp
            """
            result = session.run(query, 
                agent_name=agent_name,
                memory_type=memory_type,
                content=json.dumps(content)
            )
            return result.single()["timestamp"]
    
    async def write_shared_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any], confidence: float = 1.0):
        """Write to shared global context"""
        with self.driver.session() as session:
            query = """
            MERGE (a:Agent {name: $agent_name})
            CREATE (m:SharedMemory {
                type: $memory_type,
                content: $content,
                confidence: $confidence,
                timestamp: datetime(),
                author: $agent_name
            })
            CREATE (a)-[:CONTRIBUTED_TO_SHARED]->(m)
            RETURN m.timestamp as timestamp
            """
            result = session.run(query,
                agent_name=agent_name,
                memory_type=memory_type,
                content=json.dumps(content),
                confidence=confidence
            )
            return result.single()["timestamp"]
    
    async def query_private_memory(self, agent_name: str, memory_type: Optional[str] = None) -> List[Dict]:
        """Query agent's private memory"""
        with self.driver.session() as session:
            if memory_type:
                query = """
                MATCH (a:Agent {name: $agent_name})-[:HAS_PRIVATE_MEMORY]->(m:PrivateMemory {type: $memory_type})
                RETURN m.content as content, m.timestamp as timestamp, m.type as type
                ORDER BY m.timestamp DESC
                """
                result = session.run(query, agent_name=agent_name, memory_type=memory_type)
            else:
                query = """
                MATCH (a:Agent {name: $agent_name})-[:HAS_PRIVATE_MEMORY]->(m:PrivateMemory)
                RETURN m.content as content, m.timestamp as timestamp, m.type as type
                ORDER BY m.timestamp DESC
                """
                result = session.run(query, agent_name=agent_name)
            
            return [{"content": json.loads(record["content"]), 
                    "timestamp": record["timestamp"], 
                    "type": record["type"]} for record in result]
    
    async def query_shared_memory(self, memory_type: Optional[str] = None, min_confidence: float = 0.0) -> List[Dict]:
        """Query shared global context"""
        with self.driver.session() as session:
            if memory_type:
                query = """
                MATCH (m:SharedMemory {type: $memory_type})
                WHERE m.confidence >= $min_confidence
                RETURN m.content as content, m.timestamp as timestamp, m.author as author, m.confidence as confidence
                ORDER BY m.timestamp DESC
                """
                result = session.run(query, memory_type=memory_type, min_confidence=min_confidence)
            else:
                query = """
                MATCH (m:SharedMemory)
                WHERE m.confidence >= $min_confidence
                RETURN m.content as content, m.timestamp as timestamp, m.author as author, m.confidence as confidence, m.type as type
                ORDER BY m.timestamp DESC
                """
                result = session.run(query, min_confidence=min_confidence)
            
            return [{"content": json.loads(record["content"]),
                    "timestamp": record["timestamp"],
                    "author": record["author"],
                    "confidence": record["confidence"],
                    "type": record.get("type")} for record in result]
    
    async def get_graph_state(self) -> Dict[str, Any]:
        """Get current state of the memory graph"""
        with self.driver.session() as session:
            # Get agents and their memory counts
            agents_query = """
            MATCH (a:Agent)
            OPTIONAL MATCH (a)-[:HAS_PRIVATE_MEMORY]->(pm:PrivateMemory)
            OPTIONAL MATCH (a)-[:CONTRIBUTED_TO_SHARED]->(sm:SharedMemory)
            RETURN a.name as agent, count(pm) as private_count, count(sm) as shared_count
            """
            agents_result = session.run(agents_query)
            
            # Get recent shared memories
            shared_query = """
            MATCH (m:SharedMemory)
            RETURN m.type as type, m.author as author, m.timestamp as timestamp
            ORDER BY m.timestamp DESC LIMIT 10
            """
            shared_result = session.run(shared_query)
            
            return {
                "agents": [{"name": record["agent"], 
                           "private_memories": record["private_count"],
                           "shared_contributions": record["shared_count"]} 
                          for record in agents_result],
                "recent_shared": [{"type": record["type"],
                                 "author": record["author"],
                                 "timestamp": record["timestamp"]} 
                                for record in shared_result]
            }
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()