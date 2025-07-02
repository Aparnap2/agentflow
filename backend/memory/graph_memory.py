"""
Neo4j Graph Memory using Graphiti for agent relationships and context
"""

from typing import Dict, List, Any, Optional
import os
from datetime import datetime
from neo4j import GraphDatabase
from loguru import logger

class GraphMemory:
    """Neo4j-based graph memory for complex agent relationships"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self._create_constraints()
            logger.info("Connected to Neo4j graph database")
        except Exception as e:
            logger.warning(f"Neo4j connection failed, using fallback: {e}")
            self.driver = None
    
    def _create_constraints(self):
        """Create necessary constraints and indexes"""
        if not self.driver:
            return
            
        constraints = [
            "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT output_id IF NOT EXISTS FOR (o:Output) REQUIRE o.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    pass  # Constraint might already exist
    
    async def store_agent_relationship(self, agent_name: str, task_id: str, 
                                     output_data: Dict[str, Any], 
                                     relationships: List[Dict[str, str]] = None):
        """Store agent task execution with relationships"""
        if not self.driver:
            return self._fallback_storage(agent_name, task_id, output_data)
        
        with self.driver.session() as session:
            # Create agent node
            session.run("""
                MERGE (a:Agent {id: $agent_name})
                SET a.name = $agent_name, a.updated_at = $timestamp
            """, agent_name=agent_name, timestamp=datetime.now().isoformat())
            
            # Create task node
            session.run("""
                MERGE (t:Task {id: $task_id})
                SET t.agent = $agent_name, t.created_at = $timestamp
            """, task_id=task_id, agent_name=agent_name, timestamp=datetime.now().isoformat())
            
            # Create output node
            output_id = f"{agent_name}_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session.run("""
                CREATE (o:Output {id: $output_id})
                SET o.data = $data, o.confidence = $confidence, o.created_at = $timestamp
            """, output_id=output_id, data=str(output_data), 
                confidence=output_data.get('confidence', 0.8), 
                timestamp=datetime.now().isoformat())
            
            # Create relationships
            session.run("""
                MATCH (a:Agent {id: $agent_name}), (t:Task {id: $task_id}), (o:Output {id: $output_id})
                CREATE (a)-[:EXECUTED]->(t)
                CREATE (t)-[:PRODUCED]->(o)
            """, agent_name=agent_name, task_id=task_id, output_id=output_id)
            
            # Add custom relationships
            if relationships:
                for rel in relationships:
                    session.run(f"""
                        MATCH (from {{id: $from_id}}), (to {{id: $to_id}})
                        CREATE (from)-[:{rel['type']}]->(to)
                    """, from_id=rel['from'], to_id=rel['to'])
    
    async def get_agent_context(self, agent_name: str, depth: int = 2) -> Dict[str, Any]:
        """Get agent context with related nodes"""
        if not self.driver:
            return {"agent": agent_name, "context": "fallback_mode"}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Agent {id: $agent_name})-[:EXECUTED]->(t:Task)-[:PRODUCED]->(o:Output)
                RETURN t.id as task_id, o.data as output_data, o.confidence as confidence
                ORDER BY o.created_at DESC
                LIMIT 10
            """, agent_name=agent_name)
            
            context = {
                "agent": agent_name,
                "recent_outputs": [
                    {
                        "task_id": record["task_id"],
                        "data": record["output_data"],
                        "confidence": record["confidence"]
                    }
                    for record in result
                ]
            }
            
            return context
    
    def _fallback_storage(self, agent_name: str, task_id: str, output_data: Dict[str, Any]):
        """Fallback storage when Neo4j is unavailable"""
        logger.info(f"Storing {agent_name} task {task_id} in fallback mode")
        return {"stored": True, "mode": "fallback"}
    
    async def write_shared_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any], confidence: float = 1.0) -> str:
        """Write shared memory to graph database"""
        if not self.driver:
            return datetime.now().isoformat()
        
        timestamp = datetime.now().isoformat()
        output_id = f"{agent_name}_{memory_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.driver.session() as session:
            session.run("""
                CREATE (o:Output {id: $output_id})
                SET o.data = $data,
                    o.type = $type,
                    o.confidence = $confidence,
                    o.created_at = $timestamp,
                    o.agent = $agent_name
            """, output_id=output_id,
                 data=str(content),
                 type=memory_type,
                 confidence=confidence,
                 timestamp=timestamp,
                 agent_name=agent_name)
        
        return timestamp
    
    async def query_shared_memory(self, memory_type: str = None, min_confidence: float = 0.0, limit: int = 10) -> List[Dict[str, Any]]:
        """Query shared memory for relevant context"""
        if not self.driver:
            return [{"status": "fallback_mode", "data": {}}]
        
        with self.driver.session() as session:
            if memory_type:
                # Query specific type of outputs with confidence filter
                result = session.run("""
                    MATCH (o:Output)
                    WHERE o.type = $type AND o.confidence >= $min_confidence
                    RETURN o.data as data, o.confidence as confidence,
                           o.created_at as timestamp, o.type as type,
                           o.agent as author
                    ORDER BY o.created_at DESC
                    LIMIT $limit
                """, type=memory_type, min_confidence=min_confidence, limit=limit)
            else:
                # Query all recent outputs with confidence filter
                result = session.run("""
                    MATCH (o:Output)
                    WHERE o.confidence >= $min_confidence
                    RETURN o.data as data, o.confidence as confidence,
                           o.created_at as timestamp, o.type as type,
                           o.agent as author
                    ORDER BY o.created_at DESC
                    LIMIT $limit
                """, min_confidence=min_confidence, limit=limit)
            
            return [{
                "content": record["data"],
                "confidence": record["confidence"],
                "timestamp": record["timestamp"],
                "type": record["type"],
                "author": record["author"]
            } for record in result]
    
    async def write_private_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any]) -> str:
        """Write private memory to graph database"""
        if not self.driver:
            return datetime.now().isoformat()
        
        timestamp = datetime.now().isoformat()
        output_id = f"private_{agent_name}_{memory_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.driver.session() as session:
            session.run("""
                CREATE (o:Output:Private {id: $output_id})
                SET o.data = $data,
                    o.type = $type,
                    o.created_at = $timestamp,
                    o.agent = $agent_name
            """, output_id=output_id,
                 data=str(content),
                 type=memory_type,
                 timestamp=timestamp,
                 agent_name=agent_name)
        
        return timestamp
    
    async def query_private_memory(self, agent_name: str, memory_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Query private memory for an agent"""
        if not self.driver:
            return [{"status": "fallback_mode", "data": {}}]
        
        with self.driver.session() as session:
            if memory_type:
                result = session.run("""
                    MATCH (o:Output:Private)
                    WHERE o.agent = $agent_name AND o.type = $type
                    RETURN o.data as data, o.created_at as timestamp, o.type as type
                    ORDER BY o.created_at DESC
                    LIMIT $limit
                """, agent_name=agent_name, type=memory_type, limit=limit)
            else:
                result = session.run("""
                    MATCH (o:Output:Private)
                    WHERE o.agent = $agent_name
                    RETURN o.data as data, o.created_at as timestamp, o.type as type
                    ORDER BY o.created_at DESC
                    LIMIT $limit
                """, agent_name=agent_name, limit=limit)
            
            return [{
                "content": record["data"],
                "timestamp": record["timestamp"],
                "type": record["type"]
            } for record in result]
    
    async def get_graph_state(self) -> Dict[str, Any]:
        """Get current state of the graph"""
        if not self.driver:
            return {
                "agents": [],
                "recent_shared": [],
                "status": "fallback_mode"
            }
        
        with self.driver.session() as session:
            # Get agent statistics
            agents_result = session.run("""
                MATCH (a:Agent)
                OPTIONAL MATCH (a)-[:EXECUTED]->(t:Task)-[:PRODUCED]->(o:Output)
                OPTIONAL MATCH (o:Output {agent: a.id})
                RETURN a.id as name,
                       count(DISTINCT CASE WHEN 'Private' IN labels(o) THEN o END) as private_memories,
                       count(DISTINCT CASE WHEN NOT 'Private' IN labels(o) THEN o END) as shared_contributions
            """)
            
            agents = [{
                "name": record["name"],
                "private_memories": record["private_memories"],
                "shared_contributions": record["shared_contributions"]
            } for record in agents_result]
            
            # Get recent shared memories
            recent_result = session.run("""
                MATCH (o:Output)
                WHERE NOT 'Private' IN labels(o)
                RETURN o.data as data, o.type as type, o.agent as author,
                       o.confidence as confidence, o.created_at as timestamp
                ORDER BY o.created_at DESC
                LIMIT 5
            """)
            
            recent_shared = [{
                "content": record["data"],
                "type": record["type"],
                "author": record["author"],
                "confidence": record["confidence"],
                "timestamp": record["timestamp"]
            } for record in recent_result]
            
            return {
                "agents": agents,
                "recent_shared": recent_shared,
                "status": "active"
            }
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
