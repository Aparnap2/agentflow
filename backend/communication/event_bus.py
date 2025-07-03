"""
Event-Driven Inter-Agent Communication System
"""
import asyncio
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class AgentEvent:
    id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    event_type: str  # 'update', 'interrupt', 'request', 'response'
    content: Dict[str, Any]
    timestamp: datetime
    requires_response: bool = False

class AgentEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_log: List[AgentEvent] = []
        self.shared_context: Dict[str, Any] = {}
        self.active_agents: Dict[str, bool] = {}
    
    async def publish(self, event: AgentEvent):
        """Publish event to subscribers"""
        self.event_log.append(event)
        
        # Update shared context if event contains context updates
        if 'context_update' in event.content:
            self.shared_context.update(event.content['context_update'])
        
        # Notify subscribers
        if event.to_agent:
            # Direct message
            if event.to_agent in self.subscribers:
                for callback in self.subscribers[event.to_agent]:
                    await callback(event)
        else:
            # Broadcast to all subscribers except sender
            for agent_id, callbacks in self.subscribers.items():
                if agent_id != event.from_agent:
                    for callback in callbacks:
                        await callback(event)
    
    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to events"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        self.active_agents[agent_id] = True
    
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
    
    def get_shared_context(self) -> Dict[str, Any]:
        """Get current shared context"""
        return self.shared_context.copy()
    
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
            "active_agents": list(self.active_agents.keys())
        }

# Global event bus instance
event_bus = AgentEventBus()