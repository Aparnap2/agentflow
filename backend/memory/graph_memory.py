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
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()