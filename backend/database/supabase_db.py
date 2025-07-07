"""
Supabase Database Integration
"""
import os
from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime

class SupabaseDB:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not all([self.supabase_url, self.supabase_key]):
            self.demo_mode = True
            self.demo_data = {}
        else:
            self.demo_mode = False
    
    async def create_project(self, user_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project"""
        project = {
            "id": f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "name": project_data.get("name", "Untitled Project"),
            "vision": project_data.get("vision", ""),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            **project_data
        }
        
        if self.demo_mode:
            if "projects" not in self.demo_data:
                self.demo_data["projects"] = []
            self.demo_data["projects"].append(project)
            return project
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/projects",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json=project
                )
                
                if response.status_code in [200, 201]:
                    return response.json()[0] if isinstance(response.json(), list) else response.json()
                else:
                    return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's projects"""
        if self.demo_mode:
            return self.demo_data.get("projects", [])
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/projects?user_id=eq.{user_id}",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return []
        except Exception as e:
            return []
    
    async def save_agent_output(self, project_id: str, agent_name: str, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save agent output to database"""
        agent_output = {
            "id": f"output_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "project_id": project_id,
            "agent_name": agent_name,
            "output_data": output_data,
            "confidence": output_data.get("confidence", 0.0),
            "created_at": datetime.now().isoformat()
        }
        
        if self.demo_mode:
            if "agent_outputs" not in self.demo_data:
                self.demo_data["agent_outputs"] = []
            self.demo_data["agent_outputs"].append(agent_output)
            return agent_output
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/agent_outputs",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json=agent_output
                )
                
                if response.status_code in [200, 201]:
                    return response.json()[0] if isinstance(response.json(), list) else response.json()
                else:
                    return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

# Global database instance
supabase_db = SupabaseDB()