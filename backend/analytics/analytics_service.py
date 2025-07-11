"""
Analytics service for tracking agent performance and user interactions
Integrates with Mixpanel free tier for basic analytics
"""
import os
import json
import time
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

class AnalyticsService:
    """Analytics service for tracking agent performance and user interactions"""
    
    def __init__(self):
        self.mixpanel_token = os.getenv("MIXPANEL_TOKEN", "")
        self.mixpanel_api_url = "https://api.mixpanel.com"
        self.mixpanel_enabled = bool(self.mixpanel_token)
        
        # Local analytics storage for when Mixpanel is not available
        self.local_events = []
        self.local_metrics = {
            "agent_executions": {},
            "task_completions": 0,
            "avg_confidence": 0.0,
            "user_interactions": 0,
            "error_count": 0
        }
        
        # HTTP client for API calls
        self.client = httpx.AsyncClient(timeout=10.0)
        
        if self.mixpanel_enabled:
            logger.info("Analytics service initialized with Mixpanel integration")
        else:
            logger.info("Analytics service initialized in local-only mode")
    
    async def track_event(self, event_name: str, properties: Dict[str, Any], user_id: str = "anonymous"):
        """Track an event in the analytics system"""
        # Add common properties
        properties.update({
            "timestamp": datetime.now().isoformat(),
            "distinct_id": user_id,
            "service": "agentflow"
        })
        
        # Store locally
        self.local_events.append({
            "event": event_name,
            "properties": properties,
            "time": time.time()
        })
        
        # Update local metrics
        self._update_local_metrics(event_name, properties)
        
        # Send to Mixpanel if enabled
        if self.mixpanel_enabled:
            try:
                await self._send_to_mixpanel(event_name, properties)
            except Exception as e:
                logger.warning(f"Failed to send event to Mixpanel: {e}")
    
    async def track_agent_execution(self, agent_name: str, task_type: str, 
                                  execution_time: float, confidence: float, 
                                  success: bool, user_id: str = "anonymous"):
        """Track agent execution metrics"""
        await self.track_event(
            event_name="agent_execution",
            properties={
                "agent_name": agent_name,
                "task_type": task_type,
                "execution_time": execution_time,
                "confidence": confidence,
                "success": success
            },
            user_id=user_id
        )
    
    async def track_user_interaction(self, interaction_type: str, content_length: int,
                                   response_time: float, user_id: str = "anonymous"):
        """Track user interaction metrics"""
        await self.track_event(
            event_name="user_interaction",
            properties={
                "interaction_type": interaction_type,
                "content_length": content_length,
                "response_time": response_time
            },
            user_id=user_id
        )
    
    async def track_error(self, error_type: str, agent_name: str = None, 
                        recoverable: bool = True, user_id: str = "anonymous"):
        """Track error metrics"""
        await self.track_event(
            event_name="error",
            properties={
                "error_type": error_type,
                "agent_name": agent_name,
                "recoverable": recoverable
            },
            user_id=user_id
        )
    
    async def get_agent_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        # Calculate metrics from local events
        metrics = {
            "total_executions": 0,
            "avg_execution_time": 0.0,
            "avg_confidence": 0.0,
            "success_rate": 0.0,
            "agents": {}
        }
        
        # Filter agent execution events
        agent_events = [e for e in self.local_events if e["event"] == "agent_execution"]
        
        if not agent_events:
            return metrics
        
        # Calculate overall metrics
        metrics["total_executions"] = len(agent_events)
        metrics["avg_execution_time"] = sum(e["properties"].get("execution_time", 0) for e in agent_events) / len(agent_events)
        metrics["avg_confidence"] = sum(e["properties"].get("confidence", 0) for e in agent_events) / len(agent_events)
        metrics["success_rate"] = sum(1 for e in agent_events if e["properties"].get("success", False)) / len(agent_events)
        
        # Calculate per-agent metrics
        agent_data = {}
        for event in agent_events:
            agent_name = event["properties"].get("agent_name", "unknown")
            if agent_name not in agent_data:
                agent_data[agent_name] = {
                    "executions": 0,
                    "execution_times": [],
                    "confidences": [],
                    "successes": 0
                }
            
            agent_data[agent_name]["executions"] += 1
            agent_data[agent_name]["execution_times"].append(event["properties"].get("execution_time", 0))
            agent_data[agent_name]["confidences"].append(event["properties"].get("confidence", 0))
            if event["properties"].get("success", False):
                agent_data[agent_name]["successes"] += 1
        
        # Format agent metrics
        for agent_name, data in agent_data.items():
            metrics["agents"][agent_name] = {
                "executions": data["executions"],
                "avg_execution_time": sum(data["execution_times"]) / len(data["execution_times"]) if data["execution_times"] else 0,
                "avg_confidence": sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0,
                "success_rate": data["successes"] / data["executions"] if data["executions"] > 0 else 0
            }
        
        return metrics
    
    async def get_user_interaction_metrics(self) -> Dict[str, Any]:
        """Get user interaction metrics"""
        # Filter user interaction events
        interaction_events = [e for e in self.local_events if e["event"] == "user_interaction"]
        
        metrics = {
            "total_interactions": len(interaction_events),
            "avg_response_time": 0.0,
            "avg_content_length": 0.0,
            "interaction_types": {}
        }
        
        if not interaction_events:
            return metrics
        
        # Calculate overall metrics
        metrics["avg_response_time"] = sum(e["properties"].get("response_time", 0) for e in interaction_events) / len(interaction_events)
        metrics["avg_content_length"] = sum(e["properties"].get("content_length", 0) for e in interaction_events) / len(interaction_events)
        
        # Calculate per-type metrics
        type_data = {}
        for event in interaction_events:
            interaction_type = event["properties"].get("interaction_type", "unknown")
            if interaction_type not in type_data:
                type_data[interaction_type] = {
                    "count": 0,
                    "response_times": [],
                    "content_lengths": []
                }
            
            type_data[interaction_type]["count"] += 1
            type_data[interaction_type]["response_times"].append(event["properties"].get("response_time", 0))
            type_data[interaction_type]["content_lengths"].append(event["properties"].get("content_length", 0))
        
        # Format type metrics
        for interaction_type, data in type_data.items():
            metrics["interaction_types"][interaction_type] = {
                "count": data["count"],
                "avg_response_time": sum(data["response_times"]) / len(data["response_times"]) if data["response_times"] else 0,
                "avg_content_length": sum(data["content_lengths"]) / len(data["content_lengths"]) if data["content_lengths"] else 0
            }
        
        return metrics
    
    async def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics"""
        # Filter error events
        error_events = [e for e in self.local_events if e["event"] == "error"]
        
        metrics = {
            "total_errors": len(error_events),
            "recoverable_errors": sum(1 for e in error_events if e["properties"].get("recoverable", False)),
            "error_types": {},
            "agent_errors": {}
        }
        
        if not error_events:
            return metrics
        
        # Calculate per-type metrics
        for event in error_events:
            error_type = event["properties"].get("error_type", "unknown")
            agent_name = event["properties"].get("agent_name", "unknown")
            
            # Count by error type
            if error_type not in metrics["error_types"]:
                metrics["error_types"][error_type] = 0
            metrics["error_types"][error_type] += 1
            
            # Count by agent
            if agent_name not in metrics["agent_errors"]:
                metrics["agent_errors"][agent_name] = 0
            metrics["agent_errors"][agent_name] += 1
        
        return metrics
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all analytics metrics"""
        agent_metrics = await self.get_agent_performance_metrics()
        interaction_metrics = await self.get_user_interaction_metrics()
        error_metrics = await self.get_error_metrics()
        
        return {
            "agent_performance": agent_metrics,
            "user_interactions": interaction_metrics,
            "errors": error_metrics,
            "generated_at": datetime.now().isoformat()
        }
    
    def _update_local_metrics(self, event_name: str, properties: Dict[str, Any]):
        """Update local metrics based on event"""
        if event_name == "agent_execution":
            agent_name = properties.get("agent_name", "unknown")
            if agent_name not in self.local_metrics["agent_executions"]:
                self.local_metrics["agent_executions"][agent_name] = 0
            self.local_metrics["agent_executions"][agent_name] += 1
            
            if properties.get("success", False):
                self.local_metrics["task_completions"] += 1
            
            # Update average confidence
            old_avg = self.local_metrics["avg_confidence"]
            old_count = sum(self.local_metrics["agent_executions"].values()) - 1
            new_confidence = properties.get("confidence", 0.0)
            
            if old_count > 0:
                self.local_metrics["avg_confidence"] = (old_avg * old_count + new_confidence) / (old_count + 1)
            else:
                self.local_metrics["avg_confidence"] = new_confidence
                
        elif event_name == "user_interaction":
            self.local_metrics["user_interactions"] += 1
            
        elif event_name == "error":
            self.local_metrics["error_count"] += 1
    
    async def _send_to_mixpanel(self, event_name: str, properties: Dict[str, Any]):
        """Send event to Mixpanel"""
        if not self.mixpanel_enabled:
            return
            
        # Prepare data for Mixpanel
        data = {
            "event": event_name,
            "properties": {
                "token": self.mixpanel_token,
                **properties
            }
        }
        
        # Send to Mixpanel track endpoint
        encoded_data = json.dumps(data)
        import base64
        encoded_data = base64.b64encode(encoded_data.encode()).decode()
        
        async with self.client as client:
            response = await client.get(
                f"{self.mixpanel_api_url}/track",
                params={"data": encoded_data}
            )
            
            if response.status_code != 200 or response.text != "1":
                logger.warning(f"Mixpanel API error: {response.status_code} - {response.text}")
    
    async def close(self):
        """Close the analytics service"""
        await self.client.aclose()

# Global analytics service instance
analytics_service = AnalyticsService()