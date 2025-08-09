"""
Task Router - Intelligent task routing to appropriate agents
Enhanced version with context-aware routing and performance optimization
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from loguru import logger
import json
import re
import heapq
from collections import defaultdict

class TaskRouter:
    """Routes tasks to appropriate specialized agents based on domain expertise"""
    
    def __init__(self, memory_manager=None, event_bus=None):
        self.memory_manager = memory_manager
        self.event_bus = event_bus
        
        # Track current agent workloads
        self.agent_workloads = {
            "Marketing": 0,
            "Finance": 0,
            "Legal": 0,
            "Strategy": 0,
            "Cofounder": 0,
            "Manager": 0
        }
        
        # Track agent specializations learned from task history
        self.agent_specializations = {
            "Marketing": set(),
            "Finance": set(),
            "Legal": set(),
            "Strategy": set(),
            "Cofounder": set(),
            "Manager": set()
        }
        
        # Default routing rules
        self.routing_rules = {
            # Content and marketing related tasks
            "content_creation": ["Marketing"],
            "blog_post": ["Marketing"],
            "social_media": ["Marketing"],
            "email_sequence": ["Marketing"],
            "marketing_strategy": ["Marketing"],
            "content_strategy": ["Marketing"],
            "brand_messaging": ["Marketing"],
            "seo_optimization": ["Marketing"],
            
            # Finance related tasks
            "financial_analysis": ["Finance"],
            "budget_planning": ["Finance"],
            "pricing_strategy": ["Finance"],
            "roi_calculation": ["Finance"],
            "financial_report": ["Finance"],
            "expense_tracking": ["Finance"],
            "revenue_projection": ["Finance"],
            "cost_analysis": ["Finance"],
            
            # Legal related tasks
            "legal_review": ["Legal"],
            "compliance_check": ["Legal"],
            "terms_of_service": ["Legal"],
            "privacy_policy": ["Legal"],
            "contract_review": ["Legal"],
            "legal_risk_assessment": ["Legal"],
            "regulatory_compliance": ["Legal"],
            "intellectual_property": ["Legal"],
            
            # Strategy related tasks
            "strategic_planning": ["Strategy"],
            "market_analysis": ["Strategy"],
            "competitive_analysis": ["Strategy"],
            "business_model": ["Strategy"],
            "growth_strategy": ["Strategy"],
            "product_roadmap": ["Strategy"],
            "market_positioning": ["Strategy"],
            "vision_development": ["Strategy"],
            
            # Executive decision tasks
            "executive_decision": ["Cofounder"],
            "company_vision": ["Cofounder"],
            "leadership_guidance": ["Cofounder"],
            "strategic_direction": ["Cofounder"],
            "investor_relations": ["Cofounder"],
            "partnership_strategy": ["Cofounder"],
            
            # Project management tasks
            "project_management": ["Manager"],
            "task_coordination": ["Manager"],
            "resource_allocation": ["Manager"],
            "timeline_planning": ["Manager"],
            "workflow_optimization": ["Manager"],
            "team_coordination": ["Manager"],
            "process_improvement": ["Manager"],
            "project_planning": ["Manager"],
            
            # Cross-functional tasks (requiring multiple agents)
            "product_launch": ["Manager", "Marketing", "Finance", "Legal"],
            "business_plan": ["Strategy", "Finance", "Marketing"],
            "investor_pitch": ["Cofounder", "Finance", "Strategy"],
            "quarterly_planning": ["Manager", "Finance", "Strategy"],
            "annual_report": ["Finance", "Marketing", "Strategy"],
            "crisis_management": ["Cofounder", "Legal", "Marketing"],
            "rebranding": ["Marketing", "Strategy", "Finance"],
            "market_expansion": ["Strategy", "Finance", "Marketing", "Legal"]
        }
        
        # Agent performance metrics for dynamic routing optimization
        self.agent_performance = {
            "Marketing": {"success_rate": 0.9, "avg_completion_time": 120, "tasks_completed": 0},
            "Finance": {"success_rate": 0.95, "avg_completion_time": 150, "tasks_completed": 0},
            "Legal": {"success_rate": 0.98, "avg_completion_time": 180, "tasks_completed": 0},
            "Strategy": {"success_rate": 0.85, "avg_completion_time": 200, "tasks_completed": 0},
            "Cofounder": {"success_rate": 0.9, "avg_completion_time": 160, "tasks_completed": 0},
            "Manager": {"success_rate": 0.92, "avg_completion_time": 140, "tasks_completed": 0}
        }
        
        # Default fallback agent
        self.fallback_agent = "Manager"
        
        # Task history for learning
        self.task_history = []
        self.max_history_size = 1000
    
    async def route_task(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Route a task to appropriate agents based on task type, content, and context
        
        Args:
            task_data: Dictionary containing task information
                - task_type: Type of task
                - content: Task content
                - priority: Task priority
                - metadata: Additional metadata
                - context_id: Optional context ID for related tasks
                
        Returns:
            List of agent names that should handle the task
        """
        task_type = task_data.get("task_type", "")
        content = task_data.get("content", "")
        priority = task_data.get("priority", "normal")
        metadata = task_data.get("metadata", {})
        context_id = task_data.get("context_id", "")
        
        # Log task routing request
        logger.info(f"Routing task: {task_type} (priority: {priority})")
        
        # Step 1: Check if task is part of an existing context/project
        if context_id and self.memory_manager:
            context_agents = await self._get_context_agents(context_id)
            if context_agents:
                logger.info(f"Task {task_type} routed to {context_agents} based on context history")
                
                # Record task for history
                self._record_task_routing(task_type, context_agents, "context_based")
                
                return context_agents
        
        # Step 2: Check if task type has explicit routing rules
        if task_type in self.routing_rules:
            # Get the base agents from routing rules
            base_agents = self.routing_rules[task_type]
            
            # Apply performance-based optimization
            optimized_agents = await self._optimize_agent_selection(base_agents, task_type, priority)
            
            logger.info(f"Task {task_type} routed to {optimized_agents} based on rules and performance")
            
            # Record task for history
            self._record_task_routing(task_type, optimized_agents, "explicit_rule_optimized")
            
            return optimized_agents
        
        # Step 3: Content-based routing using keyword analysis
        if content:
            base_agents = await self._route_by_content(content)
            if base_agents:
                # Apply performance-based optimization
                optimized_agents = await self._optimize_agent_selection(base_agents, task_type, priority)
                
                logger.info(f"Task routed to {optimized_agents} based on content analysis and performance")
                
                # Record task for history
                self._record_task_routing(task_type, optimized_agents, "content_analysis_optimized")
                
                return optimized_agents
        
        # Step 4: Check for agent preference in metadata
        if "preferred_agent" in metadata:
            preferred_agent = metadata["preferred_agent"]
            logger.info(f"Task routed to {preferred_agent} based on metadata preference")
            
            # Record task for history
            self._record_task_routing(task_type, [preferred_agent], "metadata_preference")
            
            return [preferred_agent]
        
        # Step 5: Use semantic routing if content is available
        if content and self.memory_manager:
            semantic_agents = await self._route_by_semantics(content)
            if semantic_agents:
                logger.info(f"Task routed to {semantic_agents} based on semantic analysis")
                
                # Record task for history
                self._record_task_routing(task_type, semantic_agents, "semantic_analysis")
                
                return semantic_agents
        
        # Step 6: Use fallback agent
        logger.info(f"No routing rules found for task type {task_type}, using fallback agent {self.fallback_agent}")
        
        # Record task for history
        self._record_task_routing(task_type, [self.fallback_agent], "fallback")
        
        return [self.fallback_agent]
        
    async def _get_context_agents(self, context_id: str) -> List[str]:
        """Get agents associated with a context based on previous tasks"""
        if not self.memory_manager:
            return []
            
        try:
            # Retrieve context information from memory manager
            context_data = await self.memory_manager.get_context(context_id)
            if not context_data:
                return []
                
            # Extract agents that have been involved with this context
            agents_involved = set()
            for item in context_data.get("history", []):
                if "agent" in item:
                    agents_involved.add(item["agent"])
                    
            return list(agents_involved) if agents_involved else []
        except Exception as e:
            logger.error(f"Error retrieving context agents: {str(e)}")
            return []
            
    async def _optimize_agent_selection(self, base_agents: List[str], task_type: str, priority: str) -> List[str]:
        """Optimize agent selection based on performance metrics and current workload"""
        # For high priority tasks, use the base agents without optimization
        if priority == "high" and len(base_agents) <= 2:
            return base_agents
            
        # Calculate a score for each agent based on performance and workload
        agent_scores = {}
        for agent in base_agents:
            if agent in self.agent_performance:
                perf = self.agent_performance[agent]
                
                # Calculate score based on success rate and completion time
                # Higher success rate and lower completion time = higher score
                success_weight = 0.7
                speed_weight = 0.3
                
                success_score = perf["success_rate"] * success_weight
                speed_score = (1 - (perf["avg_completion_time"] / 300)) * speed_weight  # Normalize to 0-1 range
                
                # Adjust for current workload if available
                workload_penalty = 0
                if "current_workload" in perf:
                    # More workload = higher penalty
                    workload_penalty = min(perf["current_workload"] * 0.1, 0.5)  # Cap at 0.5
                    
                final_score = success_score + speed_score - workload_penalty
                agent_scores[agent] = final_score
        
        # If we couldn't score any agents, return the base agents
        if not agent_scores:
            return base_agents
            
        # For collaborative tasks (3+ agents), keep all agents but reorder by score
        if len(base_agents) >= 3:
            return sorted(base_agents, key=lambda a: agent_scores.get(a, 0), reverse=True)
            
        # For simpler tasks, select the top 1-2 agents
        top_agents = heapq.nlargest(min(2, len(agent_scores)), 
                                   agent_scores.keys(), 
                                   key=lambda a: agent_scores[a])
                                   
        return top_agents
        
    async def _route_by_semantics(self, content: str) -> List[str]:
        """Route task based on semantic analysis using vector search"""
        if not self.memory_manager:
            return []
            
        try:
            # Use memory manager to find semantically similar past tasks
            similar_tasks = await self.memory_manager.search_similar_tasks(content, limit=5)
            
            if not similar_tasks:
                return []
                
            # Count agent occurrences in similar tasks
            agent_counts = defaultdict(int)
            for task in similar_tasks:
                for agent in task.get("agents", []):
                    agent_counts[agent] += 1
                    
            # Select agents that appeared most frequently
            if agent_counts:
                max_count = max(agent_counts.values())
                top_agents = [agent for agent, count in agent_counts.items() 
                             if count == max_count]
                return top_agents
                
        except Exception as e:
            logger.error(f"Error in semantic routing: {str(e)}")
            
        return []
    
    async def _route_by_content(self, content: str) -> List[str]:
        """Route task based on content analysis"""
        # Define keyword sets for each agent domain
        domain_keywords = {
            "Marketing": {
                "marketing", "content", "social media", "seo", "advertising", "brand", 
                "campaign", "audience", "engagement", "promotion", "outreach", "blog",
                "website", "traffic", "conversion", "copywriting", "messaging"
            },
            "Finance": {
                "finance", "budget", "cost", "revenue", "profit", "expense", "pricing",
                "roi", "investment", "funding", "financial", "money", "cash flow",
                "forecast", "projection", "balance sheet", "income statement"
            },
            "Legal": {
                "legal", "compliance", "regulation", "terms", "privacy", "contract",
                "agreement", "liability", "intellectual property", "copyright", "trademark",
                "patent", "gdpr", "ccpa", "law", "policy", "rights"
            },
            "Strategy": {
                "strategy", "market", "competitive", "business model", "growth",
                "roadmap", "vision", "mission", "objective", "goal", "swot",
                "opportunity", "threat", "positioning", "differentiation"
            },
            "Cofounder": {
                "executive", "leadership", "vision", "investor", "board", "partnership",
                "acquisition", "merger", "exit", "valuation", "funding round", "pitch",
                "venture capital", "angel investor", "strategic direction"
            },
            "Manager": {
                "project", "timeline", "milestone", "resource", "allocation", "team",
                "coordination", "workflow", "process", "efficiency", "optimization",
                "planning", "execution", "monitoring", "reporting", "delegation"
            }
        }
        
        # Count keyword matches for each domain
        domain_scores = {agent: 0 for agent in domain_keywords}
        
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Score each domain based on keyword matches
        for agent, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    domain_scores[agent] += 1
        
        # Get domains with the highest scores
        max_score = max(domain_scores.values()) if domain_scores else 0
        
        # Only consider domains with scores > 0
        if max_score > 0:
            top_agents = [agent for agent, score in domain_scores.items() if score == max_score]
            return top_agents
        
        return []
    
    async def get_task_dependencies(self, task_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Identify dependencies between tasks and agents
        
        Args:
            task_data: Dictionary containing task information
                
        Returns:
            Dictionary mapping task IDs to lists of dependent task IDs
        """
        task_id = task_data.get("task_id", "")
        task_type = task_data.get("task_type", "")
        dependencies = {}
        
        # Define common dependencies between task types
        common_dependencies = {
            "marketing_strategy": ["financial_analysis", "legal_review"],
            "pricing_strategy": ["market_analysis", "financial_analysis"],
            "product_launch": ["marketing_strategy", "legal_review", "financial_analysis"],
            "content_creation": ["brand_messaging", "legal_review"],
            "financial_report": ["expense_tracking", "revenue_projection"],
            "business_plan": ["market_analysis", "financial_projection", "marketing_strategy"]
        }
        
        if task_type in common_dependencies:
            dependent_task_types = common_dependencies[task_type]
            dependencies[task_id] = dependent_task_types
            
            logger.info(f"Identified dependencies for task {task_id} ({task_type}): {dependent_task_types}")
        
        return dependencies
    
    async def optimize_routing(self, performance_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Optimize routing rules based on performance data
        
        Args:
            performance_data: Optional dictionary containing agent performance metrics
                If None, will use internal performance data
        """
        if performance_data:
            # Update agent performance metrics
            for agent, metrics in performance_data.items():
                if agent in self.agent_performance:
                    self.agent_performance[agent].update(metrics)
        
        # Analyze task history to identify patterns
        if len(self.task_history) > 50:  # Only optimize if we have enough data
            await self._learn_from_history()
        
        logger.info("Routing rules optimized based on performance data")
    
    async def _learn_from_history(self) -> None:
        """Learn routing patterns from task history"""
        # Group tasks by type
        tasks_by_type = {}
        for task in self.task_history:
            task_type = task["task_type"]
            if task_type not in tasks_by_type:
                tasks_by_type[task_type] = []
            tasks_by_type[task_type].append(task)
        
        # For each task type, find the most successful agent
        for task_type, tasks in tasks_by_type.items():
            if len(tasks) < 5:  # Skip if not enough data
                continue
            
            # Count successful completions by agent
            success_by_agent = {}
            for task in tasks:
                agents = task["agents"]
                outcome = task.get("outcome", "unknown")
                
                if outcome == "success":
                    for agent in agents:
                        if agent not in success_by_agent:
                            success_by_agent[agent] = 0
                        success_by_agent[agent] += 1
            
            # Find agent with highest success rate
            if success_by_agent:
                best_agent = max(success_by_agent.items(), key=lambda x: x[1])[0]
                
                # Update routing rules if we found a better agent
                if task_type in self.routing_rules:
                    current_agents = self.routing_rules[task_type]
                    if best_agent not in current_agents:
                        # Add the best agent to the beginning of the list
                        self.routing_rules[task_type] = [best_agent] + current_agents
                        logger.info(f"Updated routing rule for {task_type}: added {best_agent} based on performance")
    
    def _record_task_routing(self, task_type: str, agents: List[str], routing_method: str) -> None:
        """Record task routing for learning"""
        task_record = {
            "task_type": task_type,
            "agents": agents,
            "routing_method": routing_method,
            "timestamp": datetime.now().isoformat(),
            "outcome": "pending"  # Will be updated later
        }
        
        self.task_history.append(task_record)
        
        # Limit history size
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size:]
    
    async def update_task_outcome(self, task_type: str, agents: List[str], outcome: str) -> None:
        """Update task outcome for learning"""
        # Find the most recent matching task
        for task in reversed(self.task_history):
            if task["task_type"] == task_type and set(task["agents"]) == set(agents) and task["outcome"] == "pending":
                task["outcome"] = outcome
                task["completion_time"] = datetime.now().isoformat()
                
                # Update agent performance metrics
                for agent in agents:
                    if agent in self.agent_performance:
                        self.agent_performance[agent]["tasks_completed"] += 1
                        
                        # Update success rate
                        current_rate = self.agent_performance[agent]["success_rate"]
                        tasks_completed = self.agent_performance[agent]["tasks_completed"]
                        
                        if outcome == "success":
                            # Weighted average favoring recent outcomes
                            self.agent_performance[agent]["success_rate"] = (current_rate * 0.9) + 0.1
                        else:
                            self.agent_performance[agent]["success_rate"] = (current_rate * 0.9)
                
                break
    
    async def get_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get agent performance metrics"""
        return self.agent_performance
    
    async def add_routing_rule(self, task_type: str, agents: List[str]) -> bool:
        """
        Add or update a routing rule
        
        Args:
            task_type: Type of task
            agents: List of agent names
                
        Returns:
            True if successful, False otherwise
        """
        if not task_type or not agents:
            return False
        
        self.routing_rules[task_type] = agents
        logger.info(f"Added routing rule for {task_type}: {agents}")
        return True
    
    async def remove_routing_rule(self, task_type: str) -> bool:
        """
        Remove a routing rule
        
        Args:
            task_type: Type of task
                
        Returns:
            True if successful, False otherwise
        """
        if task_type in self.routing_rules:
            del self.routing_rules[task_type]
            logger.info(f"Removed routing rule for {task_type}")
            return True
        return False
    
    async def get_routing_rules(self) -> Dict[str, List[str]]:
        """Get all routing rules"""
        return self.routing_rules
    
    async def set_fallback_agent(self, agent: str) -> bool:
        """Set fallback agent"""
        if not agent:
            return False
        
        self.fallback_agent = agent
        logger.info(f"Set fallback agent to {agent}")
        return True
        
    async def update_agent_workload(self, agent: str, change: int = 1) -> None:
        """
        Update agent workload when tasks are assigned or completed
        
        Args:
            agent: Agent name
            change: Amount to change workload by (positive for new tasks, negative for completed tasks)
        """
        if agent in self.agent_workloads:
            self.agent_workloads[agent] += change
            # Ensure workload doesn't go below 0
            self.agent_workloads[agent] = max(0, self.agent_workloads[agent])
            
            # Update performance metrics with current workload
            if agent in self.agent_performance:
                self.agent_performance[agent]["current_workload"] = self.agent_workloads[agent]
                
            # Emit event if event bus is available
            if self.event_bus:
                await self.event_bus.emit("agent_workload_changed", {
                    "agent": agent,
                    "workload": self.agent_workloads[agent]
                })
                
            logger.debug(f"Updated workload for {agent}: {self.agent_workloads[agent]}")
    
    async def get_agent_workloads(self) -> Dict[str, int]:
        """Get current workload for all agents"""
        return self.agent_workloads
    
    async def update_agent_specialization(self, agent: str, task_type: str, success: bool = True) -> None:
        """
        Update agent specialization based on task outcomes
        
        Args:
            agent: Agent name
            task_type: Type of task
            success: Whether the task was completed successfully
        """
        if agent in self.agent_specializations and success:
            self.agent_specializations[agent].add(task_type)
            logger.debug(f"Updated specialization for {agent}: added {task_type}")
    
    async def get_agent_specializations(self) -> Dict[str, Set[str]]:
        """Get specializations for all agents"""
        return self.agent_specializations
    
    async def suggest_collaborative_team(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Suggest a collaborative team of agents for complex tasks
        
        Args:
            task_data: Dictionary containing task information
                
        Returns:
            List of agent names that should collaborate on the task
        """
        task_type = task_data.get("task_type", "")
        content = task_data.get("content", "")
        complexity = task_data.get("complexity", "medium")
        
        # For simple tasks, use standard routing
        if complexity == "low":
            return await self.route_task(task_data)
        
        # For complex tasks, build a collaborative team
        primary_agents = await self.route_task(task_data)
        
        # For high complexity tasks, ensure we have agents from multiple domains
        if complexity == "high":
            # Get domains covered by primary agents
            domains_covered = set(primary_agents)
            
            # Ensure we have at least one agent from each major domain for very complex tasks
            essential_domains = ["Manager", "Strategy"]
            
            # Add essential domains not already covered
            for domain in essential_domains:
                if domain not in domains_covered:
                    primary_agents.append(domain)
            
            # Add domain-specific agents based on content analysis
            if content:
                content_agents = await self._route_by_content(content)
                for agent in content_agents:
                    if agent not in primary_agents:
                        primary_agents.append(agent)
        
        # Limit team size based on complexity
        max_team_size = 5 if complexity == "high" else 3
        if len(primary_agents) > max_team_size:
            # Prioritize agents with highest performance scores
            agent_scores = {}
            for agent in primary_agents:
                if agent in self.agent_performance:
                    perf = self.agent_performance[agent]
                    score = perf["success_rate"] * 0.7 + (1 - (perf.get("current_workload", 0) / 10)) * 0.3
                    agent_scores[agent] = score
            
            # Keep the highest scoring agents
            top_agents = heapq.nlargest(max_team_size, agent_scores.keys(), key=lambda a: agent_scores.get(a, 0))
            primary_agents = top_agents
        
        logger.info(f"Suggested collaborative team for {task_type}: {primary_agents}")
        return primary_agents