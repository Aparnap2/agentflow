"""
Enhanced Agent Logging for Workflow Visibility
"""
import json
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

class AgentLogger:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.execution_log = []
    
    def log_node_start(self, node_name: str, state: Dict[str, Any]):
        """Log when a node starts execution"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": "node_start",
            "node": node_name,
            "state_keys": list(state.keys()),
            "iteration": state.get("iteration", 0)
        }
        self.execution_log.append(entry)
        logger.info(f"🔄 [{self.agent_name}] Starting {node_name} node (iteration {state.get('iteration', 0)})")
    
    def log_node_complete(self, node_name: str, output: Dict[str, Any]):
        """Log when a node completes"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": "node_complete",
            "node": node_name,
            "output_size": len(str(output)),
            "confidence": output.get("confidence", 0.0)
        }
        self.execution_log.append(entry)
        logger.info(f"✅ [{self.agent_name}] Completed {node_name} node (confidence: {output.get('confidence', 0.0)})")
    
    def log_memory_access(self, memory_type: str, operation: str, data_size: int):
        """Log memory operations"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": "memory_access",
            "memory_type": memory_type,
            "operation": operation,
            "data_size": data_size
        }
        self.execution_log.append(entry)
        logger.info(f"🧠 [{self.agent_name}] Memory {operation}: {memory_type} ({data_size} items)")
    
    def log_llm_call(self, prompt_size: int, response_size: int, model: str):
        """Log LLM API calls"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": "llm_call",
            "model": model,
            "prompt_size": prompt_size,
            "response_size": response_size
        }
        self.execution_log.append(entry)
        logger.info(f"🤖 [{self.agent_name}] LLM call: {model} (prompt: {prompt_size}, response: {response_size})")
    
    def log_communication(self, target_agent: str, message_type: str, data: Dict[str, Any]):
        """Log inter-agent communication"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": "communication",
            "target": target_agent,
            "message_type": message_type,
            "data_keys": list(data.keys())
        }
        self.execution_log.append(entry)
        logger.info(f"📡 [{self.agent_name}] → {target_agent}: {message_type}")
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get complete execution log"""
        return self.execution_log