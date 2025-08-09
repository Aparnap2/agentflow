"""
Supabase Database Integration - Enhanced for PRD Compliance
"""
import os
from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime, timedelta
from loguru import logger

class SupabaseDB:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
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
            all_projects = self.demo_data.get("projects", [])
            return [p for p in all_projects if p.get("user_id") == user_id]
        
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

    async def save_conversation(self, user_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save conversation to database"""
        conversation = {
            "id": conversation_data.get("id", f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "user_id": user_id,
            "messages": conversation_data.get("messages", []),
            "status": conversation_data.get("status", "active"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if self.demo_mode:
            if "conversations" not in self.demo_data:
                self.demo_data["conversations"] = []
            self.demo_data["conversations"].append(conversation)
            return conversation
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/conversations",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json=conversation
                )
                
                if response.status_code in [200, 201]:
                    return response.json()[0] if isinstance(response.json(), list) else response.json()
                else:
                    return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    # PRD-Required Methods
    
    async def create_approval_request(self, workspace_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create HITL approval request"""
        approval = {
            "workspace_id": workspace_id,
            "type": approval_data.get("type"),
            "payload": approval_data.get("payload", {}),
            "requested_by": approval_data.get("agent_name"),
            "reasoning": approval_data.get("reasoning", ""),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        if self.demo_mode:
            approval["id"] = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if "approvals" not in self.demo_data:
                self.demo_data["approvals"] = []
            self.demo_data["approvals"].append(approval)
            return approval
        
        return await self._execute_query("approvals", "POST", approval)
    
    async def get_pending_approvals(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get pending approval requests for workspace"""
        if self.demo_mode:
            return [a for a in self.demo_data.get("approvals", []) 
                   if a.get("workspace_id") == workspace_id and a.get("status") == "pending"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/approvals?workspace_id=eq.{workspace_id}&status=eq.pending",
                    headers={"apikey": self.supabase_key}
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            return []
    
    async def update_approval_status(self, approval_id: str, status: str, approved_by: str, reasoning: str = "") -> Dict[str, Any]:
        """Update approval request status"""
        update_data = {
            "status": status,
            "approved_by": approved_by,
            "reasoning": reasoning,
            "updated_at": datetime.now().isoformat()
        }
        
        if self.demo_mode:
            for approval in self.demo_data.get("approvals", []):
                if approval.get("id") == approval_id:
                    approval.update(update_data)
                    return approval
            return {"error": "Approval not found"}
        
        return await self._execute_query(f"approvals?id=eq.{approval_id}", "PATCH", update_data)
    
    async def log_audit_event(self, workspace_id: str, user_id: str, agent: str, action: str, 
                            details: Dict[str, Any], sensitive: bool = False) -> Dict[str, Any]:
        """Log audit event for compliance"""
        audit_log = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "agent": agent,
            "action": action,
            "details": details,
            "sensitive_flag": sensitive
        }
        
        if self.demo_mode:
            audit_log["id"] = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if "audit_logs" not in self.demo_data:
                self.demo_data["audit_logs"] = []
            self.demo_data["audit_logs"].append(audit_log)
            return audit_log
        
        return await self._execute_query("audit_logs", "POST", audit_log)
    
    async def track_instagram_dm_compliance(self, workspace_id: str, conversation_id: str, 
                                          user_id: str) -> Dict[str, Any]:
        """Track Instagram DM compliance for 24-hour rule"""
        now = datetime.now()
        compliance_data = {
            "workspace_id": workspace_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "last_user_message_at": now.isoformat(),
            "response_window_expires_at": (now + timedelta(hours=24)).isoformat(),
            "human_agent_tag_expires_at": (now + timedelta(days=7)).isoformat(),
            "compliance_status": "active"
        }
        
        if self.demo_mode:
            if "instagram_compliance" not in self.demo_data:
                self.demo_data["instagram_compliance"] = []
            self.demo_data["instagram_compliance"].append(compliance_data)
            return compliance_data
        
        # Upsert compliance record
        return await self._execute_query("instagram_dm_compliance", "POST", compliance_data, 
                                       headers={"Prefer": "resolution=merge-duplicates"})
    
    async def get_instagram_compliance_status(self, workspace_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get Instagram DM compliance status"""
        if self.demo_mode:
            for record in self.demo_data.get("instagram_compliance", []):
                if (record.get("workspace_id") == workspace_id and 
                    record.get("conversation_id") == conversation_id):
                    return record
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/instagram_dm_compliance?workspace_id=eq.{workspace_id}&conversation_id=eq.{conversation_id}",
                    headers={"apikey": self.supabase_key}
                )
                data = response.json() if response.status_code == 200 else []
                return data[0] if data else None
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return None
    
    async def _execute_query(self, endpoint: str, method: str, data: Dict[str, Any], 
                           headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute database query with error handling"""
        try:
            default_headers = {
                "apikey": self.supabase_key,
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            if headers:
                default_headers.update(headers)
            
            async with httpx.AsyncClient() as client:
                if method == "POST":
                    response = await client.post(f"{self.supabase_url}/rest/v1/{endpoint}", 
                                               headers=default_headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(f"{self.supabase_url}/rest/v1/{endpoint}", 
                                                headers=default_headers, json=data)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return result[0] if isinstance(result, list) and result else result
                else:
                    return {"error": response.text}
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": str(e)}

# Global database instance
supabase_db = SupabaseDB()