"""
Agent Execution Logs API
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json
from datetime import datetime

router = APIRouter()

# Global log storage
agent_execution_logs = {}

def store_agent_log(agent_name: str, log_entry: Dict[str, Any]):
    """Store agent execution log"""
    if agent_name not in agent_execution_logs:
        agent_execution_logs[agent_name] = []
    
    agent_execution_logs[agent_name].append(log_entry)
    
    # Keep only last 100 entries per agent
    if len(agent_execution_logs[agent_name]) > 100:
        agent_execution_logs[agent_name] = agent_execution_logs[agent_name][-100:]

@router.get("/api/agents/{agent_name}/logs")
async def get_agent_logs(agent_name: str, limit: int = 20):
    """Get execution logs for specific agent"""
    try:
        logs = agent_execution_logs.get(agent_name, [])
        return {
            "agent": agent_name,
            "logs": logs[-limit:],
            "total_entries": len(logs),
            "last_updated": logs[-1]["timestamp"] if logs else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/agents/logs/all")
async def get_all_agent_logs(limit: int = 50):
    """Get recent logs from all agents"""
    try:
        all_logs = []
        
        for agent_name, logs in agent_execution_logs.items():
            for log in logs[-limit:]:
                all_logs.append({**log, "agent": agent_name})
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "logs": all_logs[:limit],
            "agents_active": list(agent_execution_logs.keys()),
            "total_entries": len(all_logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))