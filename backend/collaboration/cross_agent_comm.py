"""
Cross-Agent Communication Protocol - Enables structured communication between agents
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from communication.event_bus import event_bus
from memory.memory_manager import OptimizedMemoryManager

class AgentMessage(BaseModel):
    """Model for messages between agents"""
    from_agent: str = Field(..., description="Agent sending the message")
    to_agent: str = Field(..., description="Agent receiving the message")
    message_type: str = Field(..., description="Type of message (request, response, notification)")
    content: Dict[str, Any] = Field(..., description="Message content")
    request_id: Optional[str] = Field(None, description="ID for request-response pairs")
    priority: str = Field("normal", description="Message priority (high, normal, low)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class CrossAgentComm:
    """Cross-Agent Communication Protocol for structured agent interactions"""
    
    def __init__(self, memory_manager: Optional[OptimizedMemoryManager] = None):
        self.memory_manager = memory_manager
        self.pending_requests = {}
        self.message_handlers = {}
        self.conflict_resolution_strategies = {
            "marketing_strategy": self._resolve_marketing_strategy_conflict,
            "budget_allocation": self._resolve_budget_allocation_conflict,
            "legal_compliance": self._resolve_legal_compliance_conflict,
            "priority": self._resolve_priority_conflict
        }
        
        # Register for events
        event_bus.subscribe("agent_message", self._handle_agent_message)
    
    async def send_message(self, 
                         from_agent: str, 
                         to_agent: str, 
                         message_type: str, 
                         content: Dict[str, Any],
                         request_id: Optional[str] = None,
                         priority: str = "normal",
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a message from one agent to another"""
        # Create message
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            request_id=request_id or f"{from_agent}_{to_agent}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            priority=priority,
            metadata=metadata or {}
        )
        
        # Store in memory if available
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=from_agent,
                memory_type="agent_message",
                content={
                    "message": message.dict(),
                    "direction": "outgoing"
                },
                is_shared=True
            )
        
        # Publish message event
        await event_bus.publish("agent_message", message.dict())
        
        logger.info(f"Message sent from {from_agent} to {to_agent}: {message_type}")
        return message.request_id
    
    async def request_input(self, 
                          from_agent: str, 
                          to_agent: str, 
                          request_type: str, 
                          context: Dict[str, Any],
                          timeout: float = 30.0) -> Dict[str, Any]:
        """Request input from another agent with timeout"""
        request_id = await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="request",
            content={
                "request_type": request_type,
                "context": context
            },
            priority="high"
        )
        
        # Create future for response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[request_id] = future
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} from {from_agent} to {to_agent} timed out")
            # Remove pending request
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            return {"error": "timeout", "message": f"Request to {to_agent} timed out"}
    
    async def register_handler(self, agent_name: str, message_type: str, handler_func):
        """Register a handler for a specific message type"""
        if agent_name not in self.message_handlers:
            self.message_handlers[agent_name] = {}
        
        self.message_handlers[agent_name][message_type] = handler_func
        logger.info(f"Registered handler for {agent_name} - {message_type}")
    
    async def _handle_agent_message(self, message_data: Dict[str, Any]):
        """Handle incoming agent message"""
        message = AgentMessage(**message_data)
        
        # Store in memory if available
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=message.to_agent,
                memory_type="agent_message",
                content={
                    "message": message.dict(),
                    "direction": "incoming"
                },
                is_shared=True
            )
        
        # Check if this is a response to a pending request
        if message.message_type == "response" and message.request_id in self.pending_requests:
            future = self.pending_requests[message.request_id]
            if not future.done():
                future.set_result(message.content)
            
            # Remove from pending requests
            del self.pending_requests[message.request_id]
            return
        
        # Check if there's a registered handler
        if message.to_agent in self.message_handlers and message.message_type in self.message_handlers[message.to_agent]:
            handler = self.message_handlers[message.to_agent][message.message_type]
            try:
                # Call handler
                response = await handler(message.content, message.from_agent, message.request_id)
                
                # Send response if this was a request
                if message.message_type == "request" and message.request_id:
                    await self.send_message(
                        from_agent=message.to_agent,
                        to_agent=message.from_agent,
                        message_type="response",
                        content=response,
                        request_id=message.request_id
                    )
            except Exception as e:
                logger.error(f"Error handling message {message.message_type} for {message.to_agent}: {e}")
                
                # Send error response if this was a request
                if message.message_type == "request" and message.request_id:
                    await self.send_message(
                        from_agent=message.to_agent,
                        to_agent=message.from_agent,
                        message_type="response",
                        content={"error": str(e)},
                        request_id=message.request_id
                    )
    
    async def resolve_conflict(self, 
                             conflict_type: str, 
                             agents_involved: List[str], 
                             conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a conflict between agents"""
        if conflict_type in self.conflict_resolution_strategies:
            resolver = self.conflict_resolution_strategies[conflict_type]
            return await resolver(agents_involved, conflict_data)
        else:
            # Default resolution strategy
            return await self._default_conflict_resolution(agents_involved, conflict_data)
    
    async def _resolve_marketing_strategy_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict between Marketing and Strategy agents"""
        # Get perspectives from both agents
        marketing_perspective = conflict_data.get("marketing_perspective", {})
        strategy_perspective = conflict_data.get("strategy_perspective", {})
        
        # Analyze alignment with business goals
        if "business_goals" in conflict_data:
            business_goals = conflict_data["business_goals"]
            marketing_alignment = self._calculate_alignment(marketing_perspective, business_goals)
            strategy_alignment = self._calculate_alignment(strategy_perspective, business_goals)
            
            if marketing_alignment > strategy_alignment * 1.2:  # Marketing is significantly more aligned
                resolution = {
                    "resolution": "marketing_preferred",
                    "reasoning": "Marketing approach has stronger alignment with business goals",
                    "recommendation": marketing_perspective.get("recommendation", ""),
                    "alignment_scores": {
                        "marketing": marketing_alignment,
                        "strategy": strategy_alignment
                    }
                }
            elif strategy_alignment > marketing_alignment * 1.2:  # Strategy is significantly more aligned
                resolution = {
                    "resolution": "strategy_preferred",
                    "reasoning": "Strategy approach has stronger alignment with business goals",
                    "recommendation": strategy_perspective.get("recommendation", ""),
                    "alignment_scores": {
                        "marketing": marketing_alignment,
                        "strategy": strategy_alignment
                    }
                }
            else:  # Similar alignment, create hybrid approach
                resolution = {
                    "resolution": "hybrid_approach",
                    "reasoning": "Both approaches have similar alignment with business goals",
                    "recommendation": self._create_hybrid_recommendation(
                        marketing_perspective.get("recommendation", ""),
                        strategy_perspective.get("recommendation", "")
                    ),
                    "alignment_scores": {
                        "marketing": marketing_alignment,
                        "strategy": strategy_alignment
                    }
                }
        else:
            # Without business goals, default to hybrid approach
            resolution = {
                "resolution": "hybrid_approach",
                "reasoning": "No business goals provided for alignment analysis",
                "recommendation": self._create_hybrid_recommendation(
                    marketing_perspective.get("recommendation", ""),
                    strategy_perspective.get("recommendation", "")
                )
            }
        
        return resolution
    
    async def create_collaborative_decision(self,
                                          decision_id: str,
                                          topic: str,
                                          agents_involved: List[str],
                                          context: Dict[str, Any],
                                          decision_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaborative decision process"""
        if not hasattr(self, 'collaborative_decision_trees'):
            self.collaborative_decision_trees = {}
        
        decision_data = {
            "decision_id": decision_id,
            "topic": topic,
            "agents_involved": agents_involved,
            "context": context,
            "decision_criteria": decision_criteria,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "contributions": {},
            "final_decision": None
        }
        
        self.collaborative_decision_trees[decision_id] = decision_data
        
        # Notify all involved agents
        for agent in agents_involved:
            await self.send_message(
                from_agent="system",
                to_agent=agent,
                message_type="collaborative_decision_request",
                content={
                    "decision_id": decision_id,
                    "topic": topic,
                    "context": context,
                    "decision_criteria": decision_criteria
                },
                priority="high"
            )
        
        logger.info(f"Created collaborative decision {decision_id} with agents {agents_involved}")
        return decision_data
    
    async def contribute_to_decision(self,
                                   decision_id: str,
                                   agent_name: str,
                                   perspective: Dict[str, Any]) -> Dict[str, Any]:
        """Contribute to a collaborative decision"""
        if not hasattr(self, 'collaborative_decision_trees'):
            self.collaborative_decision_trees = {}
        
        if decision_id not in self.collaborative_decision_trees:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision_data = self.collaborative_decision_trees[decision_id]
        
        if agent_name not in decision_data["agents_involved"]:
            raise ValueError(f"Agent {agent_name} not involved in decision {decision_id}")
        
        # Add contribution
        decision_data["contributions"][agent_name] = {
            "perspective": perspective,
            "contributed_at": datetime.now().isoformat()
        }
        
        # Check if all agents have contributed
        all_contributed = all(
            agent in decision_data["contributions"] 
            for agent in decision_data["agents_involved"]
        )
        
        if all_contributed:
            decision_data["status"] = "ready_for_finalization"
        
        logger.info(f"Agent {agent_name} contributed to decision {decision_id}")
        return {"status": "contribution_recorded", "all_contributed": all_contributed}
    
    async def finalize_decision(self,
                              decision_id: str,
                              timeout: float = 30.0) -> Dict[str, Any]:
        """Finalize a collaborative decision"""
        if not hasattr(self, 'collaborative_decision_trees'):
            self.collaborative_decision_trees = {}
        
        if decision_id not in self.collaborative_decision_trees:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision_data = self.collaborative_decision_trees[decision_id]
        
        # Analyze contributions and create final decision
        contributions = decision_data["contributions"]
        
        if not contributions:
            return {"error": "No contributions received", "decision_id": decision_id}
        
        # Simple consensus algorithm - find common themes
        final_decision = {
            "decision_id": decision_id,
            "topic": decision_data["topic"],
            "consensus_reached": len(contributions) == len(decision_data["agents_involved"]),
            "contributing_agents": list(contributions.keys()),
            "finalized_at": datetime.now().isoformat(),
            "summary": "Decision finalized based on agent contributions"
        }
        
        # Store final decision
        decision_data["final_decision"] = final_decision
        decision_data["status"] = "completed"
        decision_data["completed_at"] = datetime.now().isoformat()
        
        # Notify all agents of the final decision
        for agent in decision_data["agents_involved"]:
            await self.send_message(
                from_agent="system",
                to_agent=agent,
                message_type="decision_finalized",
                content=final_decision,
                priority="high"
            )
        
        logger.info(f"Finalized decision {decision_id}")
        return final_decision
    
    async def create_agent_meeting(self,
                                 meeting_id: str,
                                 topic: str,
                                 agents_involved: List[str],
                                 agenda: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new agent meeting"""
        if not hasattr(self, 'agent_meetings'):
            self.agent_meetings = {}
        
        meeting_data = {
            "meeting_id": meeting_id,
            "topic": topic,
            "agents_involved": agents_involved,
            "agenda": agenda,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "decisions_made": []
        }
        
        self.agent_meetings[meeting_id] = meeting_data
        
        # Notify all involved agents
        for agent in agents_involved:
            await self.send_message(
                from_agent="system",
                to_agent=agent,
                message_type="meeting_invitation",
                content={
                    "meeting_id": meeting_id,
                    "topic": topic,
                    "agenda": agenda
                },
                priority="normal"
            )
        
        logger.info(f"Created agent meeting {meeting_id} with agents {agents_involved}")
        return meeting_data
    
    async def _resolve_budget_allocation_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict between Finance and other agents on budget allocation"""
        # Get finance perspective (always prioritized for budget matters)
        finance_perspective = conflict_data.get("finance_perspective", {})
        other_perspectives = {
            agent: conflict_data.get(f"{agent.lower()}_perspective", {})
            for agent in agents_involved if agent != "Finance"
        }
        
        # Get budget constraints
        budget_constraints = finance_perspective.get("budget_constraints", {})
        
        # Calculate ROI for each proposal
        roi_scores = {}
        for agent, perspective in other_perspectives.items():
            proposal_cost = perspective.get("proposed_budget", 0)
            expected_return = perspective.get("expected_return", 0)
            
            if proposal_cost > 0:
                roi = expected_return / proposal_cost
            else:
                roi = 0
                
            roi_scores[agent] = {
                "roi": roi,
                "proposed_budget": proposal_cost,
                "expected_return": expected_return
            }
        
        # Sort by ROI
        sorted_proposals = sorted(
            roi_scores.items(),
            key=lambda x: x[1]["roi"],
            reverse=True
        )
        
        # Allocate budget based on ROI until constraints are met
        total_budget = budget_constraints.get("total_available", 0)
        allocations = {}
        remaining_budget = total_budget
        
        for agent, proposal in sorted_proposals:
            requested = proposal["proposed_budget"]
            if requested <= remaining_budget:
                allocations[agent] = requested
                remaining_budget -= requested
            else:
                allocations[agent] = remaining_budget
                remaining_budget = 0
                break
        
        return {
            "resolution": "budget_allocated_by_roi",
            "reasoning": "Budget allocated based on ROI calculations within constraints",
            "allocations": allocations,
            "roi_scores": roi_scores,
            "total_budget": total_budget,
            "remaining_budget": remaining_budget
        }
    
    async def _resolve_legal_compliance_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict involving Legal agent (Legal always wins on compliance issues)"""
        # Get legal perspective
        legal_perspective = conflict_data.get("legal_perspective", {})
        
        # Legal compliance issues always take precedence
        compliance_issues = legal_perspective.get("compliance_issues", [])
        
        if compliance_issues:
            return {
                "resolution": "legal_compliance_required",
                "reasoning": "Legal compliance requirements must be met",
                "compliance_issues": compliance_issues,
                "required_changes": legal_perspective.get("required_changes", [])
            }
        else:
            # No compliance issues, resolve based on other factors
            return await self._default_conflict_resolution(agents_involved, conflict_data)
    
    async def _resolve_priority_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict between task priorities from different agents"""
        # Get priority scores from each agent
        priority_scores = {}
        for agent in agents_involved:
            agent_perspective = conflict_data.get(f"{agent.lower()}_perspective", {})
            priority_scores[agent] = agent_perspective.get("priority_score", 0)
        
        # Get task details
        tasks = conflict_data.get("tasks", {})
        
        # Calculate weighted priority based on agent role
        weighted_priorities = {}
        for task_id, task in tasks.items():
            # Get base priority from agent
            agent = task.get("agent", "")
            base_priority = priority_scores.get(agent, 0)
            
            # Apply weights based on task attributes
            deadline_weight = 1.5 if task.get("has_deadline", False) else 1.0
            revenue_impact_weight = 1.3 if task.get("revenue_impact", False) else 1.0
            dependency_weight = 1.2 if task.get("has_dependencies", False) else 1.0
            
            # Calculate weighted priority
            weighted_priority = base_priority * deadline_weight * revenue_impact_weight * dependency_weight
            
            weighted_priorities[task_id] = {
                "task": task.get("description", ""),
                "agent": agent,
                "base_priority": base_priority,
                "weighted_priority": weighted_priority,
                "weights": {
                    "deadline": deadline_weight,
                    "revenue_impact": revenue_impact_weight,
                    "dependencies": dependency_weight
                }
            }
        
        # Sort tasks by weighted priority
        sorted_tasks = sorted(
            weighted_priorities.items(),
            key=lambda x: x[1]["weighted_priority"],
            reverse=True
        )
        
        return {
            "resolution": "priority_ordered",
            "reasoning": "Tasks prioritized based on weighted importance factors",
            "prioritized_tasks": [
                {
                    "task_id": task_id,
                    "task": details["task"],
                    "agent": details["agent"],
                    "priority": details["weighted_priority"]
                }
                for task_id, details in sorted_tasks
            ],
            "priority_calculations": weighted_priorities
        }
    
    async def _default_conflict_resolution(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default conflict resolution strategy"""
        # Get agent roles and determine hierarchy
        agent_hierarchy = {
            "Cofounder": 5,  # Highest authority
            "Manager": 4,
            "Strategy": 3,
            "Finance": 2,
            "Legal": 2,
            "Marketing": 1
        }
        
        # Sort agents by hierarchy
        sorted_agents = sorted(
            agents_involved,
            key=lambda x: agent_hierarchy.get(x, 0),
            reverse=True
        )
        
        # Get perspective from highest authority agent
        highest_agent = sorted_agents[0]
        highest_perspective = conflict_data.get(f"{highest_agent.lower()}_perspective", {})
        
        return {
            "resolution": "authority_based",
            "reasoning": f"Resolution based on agent authority hierarchy, with {highest_agent} having highest authority",
            "recommendation": highest_perspective.get("recommendation", ""),
            "authority_agent": highest_agent
        }
    
    def _calculate_alignment(self, perspective: Dict[str, Any], business_goals: Dict[str, Any]) -> float:
        """Calculate alignment score between a perspective and business goals"""
        alignment_score = 0.0
        
        # Extract key metrics from perspective
        metrics = perspective.get("metrics", {})
        
        # Compare with business goals
        for goal_name, goal_value in business_goals.items():
            if goal_name in metrics:
                # Calculate alignment for this goal
                metric_value = metrics[goal_name]
                
                # Different calculation based on goal type
                if isinstance(goal_value, (int, float)) and isinstance(metric_value, (int, float)):
                    # Numerical goal, calculate percentage alignment
                    if goal_value != 0:
                        goal_alignment = min(metric_value / goal_value, 1.0)
                    else:
                        goal_alignment = 0.0
                elif isinstance(goal_value, str) and isinstance(metric_value, str):
                    # String goal, calculate text similarity
                    goal_alignment = self._calculate_text_similarity(goal_value, metric_value)
                else:
                    # Different types, no alignment
                    goal_alignment = 0.0
                
                # Add to overall alignment score
                alignment_score += goal_alignment
        
        # Normalize by number of goals
        if business_goals:
            alignment_score /= len(business_goals)
        
        return alignment_score
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _create_hybrid_recommendation(self, rec1: str, rec2: str) -> str:
        """Create a hybrid recommendation from two approaches"""
        # Simple implementation - in a real system this would use more sophisticated NLP
        return f"Hybrid approach combining elements from both perspectives: {rec1[:100]}... and {rec2[:100]}..."

# Global instance
cross_agent_comm = CrossAgentComm()    as
ync def _resolve_product_roadmap_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict related to product roadmap priorities"""
        # Extract perspectives from different agents
        strategy_perspective = conflict_data.get("strategy_perspective", {})
        marketing_perspective = conflict_data.get("marketing_perspective", {})
        finance_perspective = conflict_data.get("finance_perspective", {})
        
        # Get feature priorities from each agent
        feature_priorities = {}
        for feature_id, feature_data in conflict_data.get("features", {}).items():
            feature_priorities[feature_id] = {
                "name": feature_data.get("name", ""),
                "description": feature_data.get("description", ""),
                "scores": {}
            }
            
            # Collect scores from each agent
            for agent in agents_involved:
                agent_perspective = conflict_data.get(f"{agent.lower()}_perspective", {})
                agent_priorities = agent_perspective.get("feature_priorities", {})
                
                if feature_id in agent_priorities:
                    feature_priorities[feature_id]["scores"][agent] = agent_priorities[feature_id]
        
        # Calculate weighted scores based on business impact
        weighted_scores = {}
        for feature_id, feature_data in feature_priorities.items():
            # Base weights for different aspects
            weights = {
                "Strategy": 0.4,  # Strategic alignment
                "Marketing": 0.3,  # Market impact
                "Finance": 0.3,    # Financial impact
                "Legal": 0.2,      # Compliance importance
                "Cofounder": 0.5   # Executive priority
            }
            
            # Calculate weighted score
            total_weight = 0
            weighted_score = 0
            
            for agent, score in feature_data["scores"].items():
                agent_weight = weights.get(agent, 0.2)
                weighted_score += score * agent_weight
                total_weight += agent_weight
            
            # Normalize by total weight
            if total_weight > 0:
                weighted_scores[feature_id] = weighted_score / total_weight
            else:
                weighted_scores[feature_id] = 0
        
        # Sort features by weighted score
        sorted_features = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Create prioritized roadmap
        prioritized_roadmap = []
        for feature_id, score in sorted_features:
            feature_data = feature_priorities[feature_id]
            prioritized_roadmap.append({
                "feature_id": feature_id,
                "name": feature_data["name"],
                "description": feature_data["description"],
                "priority_score": score,
                "agent_scores": feature_data["scores"]
            })
        
        return {
            "resolution": "roadmap_prioritized",
            "reasoning": "Features prioritized based on weighted importance across all stakeholders",
            "prioritized_roadmap": prioritized_roadmap,
            "weighted_scores": weighted_scores
        }
    
    async def _resolve_resource_allocation_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict related to resource allocation between teams/projects"""
        # Extract resource requests from each agent
        resource_requests = {}
        for agent in agents_involved:
            agent_perspective = conflict_data.get(f"{agent.lower()}_perspective", {})
            agent_requests = agent_perspective.get("resource_requests", {})
            
            for resource_id, request in agent_requests.items():
                if resource_id not in resource_requests:
                    resource_requests[resource_id] = {
                        "name": request.get("name", ""),
                        "type": request.get("type", ""),
                        "total_available": request.get("total_available", 0),
                        "requests": {}
                    }
                
                resource_requests[resource_id]["requests"][agent] = {
                    "amount": request.get("amount", 0),
                    "priority": request.get("priority", 0),
                    "justification": request.get("justification", ""),
                    "impact": request.get("impact", 0)
                }
        
        # Allocate resources based on priority and impact
        allocations = {}
        for resource_id, resource_data in resource_requests.items():
            total_available = resource_data["total_available"]
            requests = resource_data["requests"]
            
            # Calculate priority-impact score for each request
            scored_requests = []
            for agent, request in requests.items():
                priority = request["priority"]
                impact = request["impact"]
                amount = request["amount"]
                
                # Calculate score (priority * impact)
                score = priority * impact
                
                scored_requests.append({
                    "agent": agent,
                    "amount": amount,
                    "score": score,
                    "justification": request["justification"]
                })
            
            # Sort by score
            sorted_requests = sorted(scored_requests, key=lambda x: x["score"], reverse=True)
            
            # Allocate resources
            remaining = total_available
            resource_allocations = {}
            
            for request in sorted_requests:
                agent = request["agent"]
                amount = request["amount"]
                
                if amount <= remaining:
                    # Full allocation
                    resource_allocations[agent] = amount
                    remaining -= amount
                else:
                    # Partial allocation
                    resource_allocations[agent] = remaining
                    remaining = 0
                    break
            
            allocations[resource_id] = {
                "name": resource_data["name"],
                "type": resource_data["type"],
                "total_available": total_available,
                "allocations": resource_allocations,
                "remaining": remaining
            }
        
        return {
            "resolution": "resources_allocated",
            "reasoning": "Resources allocated based on priority and impact scores",
            "allocations": allocations
        }
    
    async def _resolve_strategic_direction_conflict(self, agents_involved: List[str], conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict related to strategic direction and vision"""
        # Extract strategic proposals from each agent
        strategic_proposals = {}
        for agent in agents_involved:
            agent_perspective = conflict_data.get(f"{agent.lower()}_perspective", {})
            strategic_proposals[agent] = {
                "vision": agent_perspective.get("vision", ""),
                "goals": agent_perspective.get("goals", []),
                "metrics": agent_perspective.get("metrics", {}),
                "timeline": agent_perspective.get("timeline", {})
            }
        
        # Check if Cofounder is involved (has highest authority on vision)
        if "Cofounder" in strategic_proposals:
            # Cofounder's vision takes precedence
            cofounder_vision = strategic_proposals["Cofounder"]["vision"]
            cofounder_goals = strategic_proposals["Cofounder"]["goals"]
            
            # But incorporate metrics and timelines from other agents
            combined_metrics = {}
            combined_timeline = {}
            
            for agent, proposal in strategic_proposals.items():
                # Add metrics from each agent
                for metric_name, metric_value in proposal["metrics"].items():
                    if metric_name not in combined_metrics:
                        combined_metrics[metric_name] = {
                            "value": metric_value,
                            "source": agent
                        }
                
                # Combine timeline elements
                for milestone, timeline_data in proposal["timeline"].items():
                    if milestone not in combined_timeline:
                        combined_timeline[milestone] = timeline_data
            
            return {
                "resolution": "cofounder_vision_with_integrated_details",
                "reasoning": "Cofounder's strategic vision takes precedence, with integrated metrics and timeline details from all agents",
                "vision": cofounder_vision,
                "goals": cofounder_goals,
                "metrics": combined_metrics,
                "timeline": combined_timeline
            }
        else:
            # No Cofounder involved, create consensus vision
            # Find common elements across all proposals
            all_visions = [proposal["vision"] for proposal in strategic_proposals.values()]
            all_goals = [goal for proposal in strategic_proposals.values() for goal in proposal["goals"]]
            
            # Count goal frequencies
            goal_counts = {}
            for goal in all_goals:
                if goal in goal_counts:
                    goal_counts[goal] += 1
                else:
                    goal_counts[goal] = 1
            
            # Select goals with highest consensus
            consensus_threshold = len(agents_involved) / 2  # At least half of agents agree
            consensus_goals = [goal for goal, count in goal_counts.items() if count >= consensus_threshold]
            
            # Create hybrid vision statement
            consensus_vision = self._create_hybrid_vision(all_visions)
            
            # Combine metrics from all agents
            combined_metrics = {}
            for agent, proposal in strategic_proposals.items():
                for metric_name, metric_value in proposal["metrics"].items():
                    if metric_name not in combined_metrics:
                        combined_metrics[metric_name] = {
                            "value": metric_value,
                            "source": agent
                        }
            
            # Create consensus timeline
            consensus_timeline = self._create_consensus_timeline(
                [proposal["timeline"] for proposal in strategic_proposals.values()]
            )
            
            return {
                "resolution": "consensus_strategic_direction",
                "reasoning": "Strategic direction based on consensus elements across all agents",
                "vision": consensus_vision,
                "goals": consensus_goals,
                "metrics": combined_metrics,
                "timeline": consensus_timeline
            }
    
    def _create_hybrid_vision(self, vision_statements: List[str]) -> str:
        """Create a hybrid vision statement from multiple inputs"""
        # Simple implementation - in a real system this would use more sophisticated NLP
        if not vision_statements:
            return ""
        
        # Just concatenate the first parts of each vision for now
        combined = " ".join([v.split(".")[0] for v in vision_statements if v])
        return combined[:200] + "..."
    
    def _create_consensus_timeline(self, timelines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a consensus timeline from multiple timeline proposals"""
        # Collect all milestones
        all_milestones = {}
        for timeline in timelines:
            for milestone, data in timeline.items():
                if milestone not in all_milestones:
                    all_milestones[milestone] = []
                all_milestones[milestone].append(data)
        
        # Create consensus for each milestone
        consensus_timeline = {}
        for milestone, data_points in all_milestones.items():
            # For dates, take the median
            dates = [d.get("date") for d in data_points if d.get("date")]
            if dates:
                dates.sort()
                median_date = dates[len(dates) // 2]
            else:
                median_date = None
            
            # For descriptions, take the most detailed one
            descriptions = [d.get("description", "") for d in data_points]
            most_detailed = max(descriptions, key=len) if descriptions else ""
            
            consensus_timeline[milestone] = {
                "date": median_date,
                "description": most_detailed
            }
        
        return consensus_timeline