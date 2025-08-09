"""
Value Engine Framework - Visual systems for business scaling
Based on value engine methodology for documenting critical business processes
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class ValueEngineType(Enum):
    GROWTH = "growth"
    FULFILLMENT = "fulfillment"  
    INNOVATION = "innovation"

class ValueEngine:
    """Represents a value engine with triggering/ending events and process flow"""
    
    def __init__(self, name: str, engine_type: ValueEngineType):
        self.name = name
        self.engine_type = engine_type
        self.triggering_event = None
        self.ending_event = None
        self.process_steps = []
        self.decision_points = []
        self.power_stages = []  # Critical steps that cannot fail
        self.stakeholders = []
        
    def set_events(self, triggering_event: str, ending_event: str):
        """Define what starts and ends this value engine"""
        self.triggering_event = triggering_event
        self.ending_event = ending_event
        
    def add_process_step(self, step: Dict[str, Any]):
        """Add a process step (square in flowchart)"""
        step["type"] = "task"
        step["id"] = len(self.process_steps) + 1
        self.process_steps.append(step)
        
    def add_decision_point(self, decision: Dict[str, Any]):
        """Add a decision point (diamond in flowchart)"""
        decision["type"] = "decision"
        decision["id"] = len(self.decision_points) + 1
        self.decision_points.append(decision)
        
    def mark_power_stage(self, step_id: int, reason: str):
        """Mark a step as a power stage (critical)"""
        self.power_stages.append({
            "step_id": step_id,
            "reason": reason,
            "requires_sop": True,
            "owner": None
        })
        
    def to_flowchart_data(self) -> Dict[str, Any]:
        """Export as flowchart data for visualization"""
        return {
            "name": self.name,
            "type": self.engine_type.value,
            "triggering_event": self.triggering_event,
            "ending_event": self.ending_event,
            "nodes": self.process_steps + self.decision_points,
            "power_stages": self.power_stages,
            "stakeholders": self.stakeholders
        }

# Initialize AgentFlow value engines
def initialize_agentflow_value_engines() -> Dict[str, ValueEngine]:
    """Initialize all AgentFlow value engines"""
    growth_engine = ValueEngine("AgentFlow Growth Engine", ValueEngineType.GROWTH)
    growth_engine.set_events(
        triggering_event="Potential customer discovers AgentFlow",
        ending_event="Customer becomes paying subscriber"
    )
    
    fulfillment_engine = ValueEngine("AgentFlow Fulfillment Engine", ValueEngineType.FULFILLMENT)
    fulfillment_engine.set_events(
        triggering_event="Customer completes payment and onboarding", 
        ending_event="Customer achieves business analysis goals"
    )
    
    return {
        "growth": growth_engine,
        "fulfillment": fulfillment_engine
    }