from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import json
import os
import yaml
import json
from datetime import datetime
from loguru import logger
from pathlib import Path

class GraphMemory:
    """Neo4j-based memory system for agent collaboration with export capabilities"""
    
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
    
    async def export_to_yaml(self, output_dir: str = "./data") -> Dict[str, str]:
        """Export memory data to YAML files following PRD deliverables format"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = {}
        
        # Export shared memories by agent type following PRD naming
        shared_memories = await self.query_shared_memory()
        
        # Group memories by agent for PRD-compliant file naming
        agent_outputs = {}
        for memory in shared_memories:
            author = memory.get("author", "unknown")
            mem_type = memory.get("type", "general")
            
            if author not in agent_outputs:
                agent_outputs[author] = {}
            
            agent_outputs[author][mem_type] = {
                "content": memory["content"],
                "confidence": memory["confidence"],
                "timestamp": str(memory["timestamp"])
            }
        
        # Export files according to PRD deliverables table
        deliverable_mapping = {
            "Cofounder": "vision.yml",
            "Manager": "plan.yml",
            "Product": "product.yml",
            "Finance": "finance.yml",
            "Marketing": "marketing.yml",
            "Legal": "legal.yml"
        }
        
        for agent, filename in deliverable_mapping.items():
            if agent in agent_outputs:
                filepath = output_path / filename
                
                # Structure data according to PRD format
                export_data = {
                    "agent": agent,
                    "outputs": agent_outputs[agent],
                    "exported_at": datetime.now().isoformat(),
                    "format_version": "1.0"
                }
                
                with open(filepath, 'w') as f:
                    yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
                
                exported_files[agent.lower()] = str(filepath)
        
        # Export timeline as JSON (as specified in PRD)
        timeline_data = await self._export_timeline_data()
        timeline_filepath = output_path / "timeline.json"
        with open(timeline_filepath, 'w') as f:
            json.dump(timeline_data, f, indent=2)
        exported_files["timeline"] = str(timeline_filepath)
        
        return exported_files
    
    async def _export_timeline_data(self) -> Dict[str, Any]:
        """Export timeline data in PRD format"""
        shared_memories = await self.query_shared_memory()
        
        timeline_events = []
        for memory in shared_memories:
            timeline_events.append({
                "timestamp": str(memory["timestamp"]),
                "agent": memory["author"],
                "action": "memory_write",
                "type": memory.get("type", "unknown"),
                "confidence": memory["confidence"],
                "summary": str(memory["content"])[:100] + "..." if len(str(memory["content"])) > 100 else str(memory["content"])
            })
        
        # Sort by timestamp
        timeline_events.sort(key=lambda x: x["timestamp"])
        
        return {
            "project_timeline": timeline_events,
            "summary": {
                "total_events": len(timeline_events),
                "agents_involved": list(set(event["agent"] for event in timeline_events)),
                "exported_at": datetime.now().isoformat()
            }
        }
    
    async def export_to_graphml(self, output_path: str = "./data/graph.graphml") -> str:
        """Export memory graph to GraphML format"""
        with self.driver.session() as session:
            # Get all nodes and relationships
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            """
            result = session.run(query)
            
            # Build GraphML content
            graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="label" for="node" attr.name="label" attr.type="string"/>
  <key id="type" for="node" attr.name="type" attr.type="string"/>
  <key id="content" for="node" attr.name="content" attr.type="string"/>
  <key id="relationship" for="edge" attr.name="relationship" attr.type="string"/>
  <graph id="AgentFlowMemory" edgedefault="directed">\n'''
            
            nodes = set()
            edges = []
            
            for record in result:
                node = record["n"]
                rel = record["r"]
                target = record["m"]
                
                if node:
                    node_id = str(id(node))
                    if node_id not in nodes:
                        nodes.add(node_id)
                        node_labels = list(node.labels)
                        node_props = dict(node)
                        
                        graphml_content += f'    <node id="{node_id}">\n'
                        graphml_content += f'      <data key="label">{node_labels[0] if node_labels else "Node"}</data>\n'
                        graphml_content += f'      <data key="type">{node_props.get("type", "unknown")}</data>\n'
                        if "content" in node_props:
                            content = str(node_props["content"])[:200] + "..." if len(str(node_props["content"])) > 200 else str(node_props["content"])
                            graphml_content += f'      <data key="content">{content}</data>\n'
                        graphml_content += '    </node>\n'
                
                if rel and target:
                    source_id = str(id(node))
                    target_id = str(id(target))
                    
                    if target_id not in nodes:
                        nodes.add(target_id)
                        target_labels = list(target.labels)
                        target_props = dict(target)
                        
                        graphml_content += f'    <node id="{target_id}">\n'
                        graphml_content += f'      <data key="label">{target_labels[0] if target_labels else "Node"}</data>\n'
                        graphml_content += f'      <data key="type">{target_props.get("type", "unknown")}</data>\n'
                        if "content" in target_props:
                            content = str(target_props["content"])[:200] + "..." if len(str(target_props["content"])) > 200 else str(target_props["content"])
                            graphml_content += f'      <data key="content">{content}</data>\n'
                        graphml_content += '    </node>\n'
                    
                    edge_id = f"{source_id}_{target_id}_{rel.type}"
                    graphml_content += f'    <edge id="{edge_id}" source="{source_id}" target="{target_id}">\n'
                    graphml_content += f'      <data key="relationship">{rel.type}</data>\n'
                    graphml_content += '    </edge>\n'
            
            graphml_content += '  </graph>\n</graphml>'
            
            # Write to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(graphml_content)
            
            return output_path
    
    async def cleanup_old_exports(self, output_dir: str = "./data", keep_versions: int = 5):
        """Clean up old export files, keeping only the most recent versions"""
        output_path = Path(output_dir)
        if not output_path.exists():
            return
        
        # Group files by type (without timestamp)
        file_groups = {}
        for file_path in output_path.glob("*.yml"):
            base_name = file_path.stem.split('_')[0]  # Remove timestamp suffix
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append(file_path)
        
        # Keep only the most recent files for each type
        for file_type, files in file_groups.items():
            if len(files) > keep_versions:
                # Sort by modification time, keep newest
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_file in files[keep_versions:]:
                    old_file.unlink()
                    logger.info(f"Cleaned up old export: {old_file}")
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

    async def clear_all_memory(self):
        """
        Clears all nodes and relationships from the Neo4j database.
        USE WITH CAUTION: This will delete all your data.
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("All data cleared from Neo4j database.")