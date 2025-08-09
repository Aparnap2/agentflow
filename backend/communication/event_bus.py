"""
Event-Driven Inter-Agent Communication System
"""
import asyncio
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

@dataclass
class AgentEvent:
    id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    event_type: str  # 'update', 'interrupt', 'request', 'response'
    content: Dict[str, Any]
    timestamp: datetime
    requires_response: bool = False

class EnhancedEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.topic_subscribers: Dict[str, List[tuple]] = {}  # topic -> [(agent_id, callback)]
        self.event_log: List[AgentEvent] = []
        self.shared_context: Dict[str, Any] = {}
        self.active_agents: Dict[str, bool] = {}
        self.event_filters: Dict[str, Callable] = {}  # agent_id -> filter_function
    
    async def publish(self, event: AgentEvent):
        """Publish event to subscribers"""
        self.event_log.append(event)
        
        # Update shared context if event contains context updates
        if 'context_update' in event.content:
            self.shared_context.update(event.content['context_update'])
        
        # Handle topic-based events
        if event.event_type == "topic_update" and "topic" in event.content:
            await self.publish_to_topic(event.content["topic"], event)
            return
        
        # Notify subscribers with filtering
        if event.to_agent:
            # Direct message
            if event.to_agent in self.subscribers:
                for callback in self.subscribers[event.to_agent]:
                    if self._should_deliver_event(event.to_agent, event):
                        try:
                            await callback(event)
                        except Exception as e:
                            print(f"Error delivering event to {event.to_agent}: {e}")
        else:
            # Broadcast to all subscribers except sender
            for agent_id, callbacks in self.subscribers.items():
                if agent_id != event.from_agent and self._should_deliver_event(agent_id, event):
                    for callback in callbacks:
                        try:
                            await callback(event)
                        except Exception as e:
                            print(f"Error delivering event to {agent_id}: {e}")
    
    def _should_deliver_event(self, agent_id: str, event: AgentEvent) -> bool:
        """Check if event should be delivered to agent based on filters"""
        if agent_id in self.event_filters:
            try:
                return self.event_filters[agent_id](event)
            except Exception:
                return True  # Default to deliver if filter fails
        return True
    
    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to events"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        self.active_agents[agent_id] = True
    
    def subscribe_to_topic(self, agent_id: str, topic: str, callback: Callable):
        """Subscribe agent to specific topic"""
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = []
        self.topic_subscribers[topic].append((agent_id, callback))
        self.active_agents[agent_id] = True
    
    async def publish_to_topic(self, topic: str, event: AgentEvent):
        """Publish event to topic subscribers"""
        self.event_log.append(event)
        
        if topic in self.topic_subscribers:
            for agent_id, callback in self.topic_subscribers[topic]:
                if agent_id != event.from_agent:  # Don't send to self
                    try:
                        await callback(event)
                    except Exception as e:
                        print(f"Error delivering event to {agent_id}: {e}")
    
    def set_event_filter(self, agent_id: str, filter_func: Callable[[AgentEvent], bool]):
        """Set event filter for agent"""
        self.event_filters[agent_id] = filter_func
    
    async def send_interrupt(self, from_agent: str, to_agent: str, interrupt_data: Dict):
        """Send interrupt to specific agent"""
        event = AgentEvent(
            id=f"interrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            from_agent=from_agent,
            to_agent=to_agent,
            event_type="interrupt",
            content={
                "interrupt_type": interrupt_data.get("type", "context_update"),
                "data": interrupt_data.get("data", {}),
                "message": interrupt_data.get("message", "")
            },
            timestamp=datetime.now(),
            requires_response=interrupt_data.get("requires_response", False)
        )
        
        await self.publish(event)
    
    async def request_agent_collaboration(self, requesting_agent: str, target_agent: str, 
                                        collaboration_type: str, data: Dict[str, Any]):
        """Request collaboration between agents"""
        event = AgentEvent(
            id=f"collab_req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            from_agent=requesting_agent,
            to_agent=target_agent,
            event_type="collaboration_request",
            content={
                "collaboration_type": collaboration_type,
                "request_data": data,
                "expected_response": data.get("expected_response", "analysis")
            },
            timestamp=datetime.now(),
            requires_response=True
        )
        
        await self.publish(event)
        return event.id
    
    async def broadcast_update(self, from_agent: str, update_data: Dict):
        """Broadcast update to all agents"""
        event = AgentEvent(
            id=f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            from_agent=from_agent,
            to_agent=None,  # Broadcast
            event_type="update",
            content={
                "update_type": update_data.get("type", "status"),
                "data": update_data.get("data", {}),
                "message": update_data.get("message", "")
            },
            timestamp=datetime.now()
        )
        
        await self.publish(event)
    
    async def broadcast_to_topic(self, from_agent: str, topic: str, update_data: Dict):
        """Broadcast update to specific topic subscribers"""
        event = AgentEvent(
            id=f"topic_broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            from_agent=from_agent,
            to_agent=None,
            event_type="topic_update",
            content={
                "topic": topic,
                "update_type": update_data.get("type", "status"),
                "data": update_data.get("data", {}),
                "message": update_data.get("message", "")
            },
            timestamp=datetime.now()
        )
        
        await self.publish_to_topic(topic, event)
    
    def get_shared_context(self) -> Dict[str, Any]:
        """Get current shared context"""
        return self.shared_context.copy()
    
    def update_shared_context(self, agent_id: str, context_updates: Dict[str, Any]):
        """Update shared context from agent"""
        self.shared_context.update(context_updates)
        
        # Broadcast context update
        asyncio.create_task(self.broadcast_update(agent_id, {
            "type": "context_update",
            "data": context_updates,
            "message": f"{agent_id} updated shared context"
        }))
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication analytics"""
        total_events = len(self.event_log)
        if total_events == 0:
            return {"total_events": 0}
        
        event_types = {}
        agent_activity = {}
        
        for event in self.event_log:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            agent_activity[event.from_agent] = agent_activity.get(event.from_agent, 0) + 1
        
        return {
            "total_events": total_events,
            "event_types": event_types,
            "agent_activity": agent_activity,
            "active_agents": list(self.active_agents.keys()),
            "topic_subscriptions": {topic: len(subs) for topic, subs in self.topic_subscribers.items()}
        }
    
    async def create_agent_collaboration(self, agents: List[str], collaboration_topic: str):
        """Create collaboration channel for specific agents"""
        collaboration_event = AgentEvent(
            id=f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            from_agent="system",
            to_agent=None,
            event_type="collaboration_start",
            content={
                "collaboration_topic": collaboration_topic,
                "participating_agents": agents,
                "channel_id": f"collab_{collaboration_topic}_{len(agents)}"
            },
            timestamp=datetime.now()
        )
        
        # Subscribe all agents to the collaboration topic
        for agent in agents:
            if agent in self.subscribers:
                for callback in self.subscribers[agent]:
                    self.subscribe_to_topic(agent, collaboration_topic, callback)
        
        await self.publish_to_topic(collaboration_topic, collaboration_event)
        return collaboration_event.content["channel_id"]

# Backward compatibility alias
AgentEventBus = EnhancedEventBus

# Global enhanced event bus instance
event_bus = EnhancedEventBus()

# Slack notification integration following PRD architecture
async def send_slack_notification_via_event_bus(agent_name: str, event_type: str, message: str, priority: str = "normal", channel: str = "#agent-updates"):
    """Send Slack notification through event bus - PRD compliant"""
    await event_bus.broadcast_to_topic(agent_name, "slack_notifications", {
        "type": "slack_notification",
        "data": {
            "agent_name": agent_name,
            "event_type": event_type,
            "message": message,
            "priority": priority,
            "channel": channel,
            "timestamp": datetime.now().isoformat()
        },
        "message": f"Slack notification from {agent_name}: {event_type}"
    })

# Enhanced notification helpers for different agent types
async def send_marketing_slack_notification(event_type: str, message: str, priority: str = "normal"):
    """Send marketing-specific Slack notification"""
    await send_slack_notification_via_event_bus(
        agent_name="Marketing Intelligence",
        event_type=event_type,
        message=f"🎯 {message}",
        priority=priority,
        channel="#marketing-updates"
    )

async def send_instagram_automation_notification(action: str, details: str):
    """Send Instagram automation notification"""
    await send_marketing_slack_notification(
        event_type="instagram_automation",
        message=f"Instagram {action}: {details}",
        priority="low"
    )

async def send_workflow_completion_notification(workflow_name: str, agent_name: str, success: bool):
    """Send workflow completion notification"""
    status_emoji = "✅" if success else "❌"
    priority = "normal" if success else "high"
    
    await send_slack_notification_via_event_bus(
        agent_name=agent_name,
        event_type="workflow_completion",
        message=f"{status_emoji} Workflow '{workflow_name}' {'completed successfully' if success else 'failed'}",
        priority=priority,
        channel="#workflow-updates"
    )