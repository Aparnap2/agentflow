"""
Test script for the enhanced manager agent
"""

import asyncio
import json
from loguru import logger

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from communication.event_bus import event_bus
from agents.enhanced_manager_agent import EnhancedManagerAgent

async def test_enhanced_manager():
    """Test the enhanced manager agent"""
    # Initialize memory and approval managers
    memory_manager = MemoryManager()
    approval_manager = ApprovalManager()
    
    # Initialize enhanced manager agent
    manager = EnhancedManagerAgent(memory_manager, approval_manager, event_bus)
    
    # Test task routing
    print("\n=== Testing Task Routing ===")
    routing_result = await manager.route_task({
        "task_type": "content_creation",
        "content": "Create a blog post about AI productivity tools",
        "priority": "high"
    })
    print(f"Assigned agents: {routing_result['assigned_agents']}")
    print(f"Task assignments: {json.dumps(routing_result['task_assignments'], indent=2)}")
    
    # Test cross-agent validation
    print("\n=== Testing Cross-Agent Validation ===")
    validation_result = await manager.validate_cross_agent_results(
        results={
            "Marketing": "AI productivity tools can significantly boost efficiency in the workplace.",
            "Finance": "AI productivity tools offer a strong ROI by reducing manual labor costs.",
            "Legal": "When implementing AI productivity tools, ensure compliance with data privacy regulations."
        },
        agents_involved=["Marketing", "Finance", "Legal"]
    )
    print(f"Validation valid: {validation_result['is_valid']}")
    print(f"Validation confidence: {validation_result['confidence']}")
    print(f"Consensus result: {validation_result['consensus_result']}")
    
    # Test multi-agent project management
    print("\n=== Testing Multi-Agent Project Management ===")
    project_result = await manager.manage_multi_agent_project(
        project_id="test_project_001",
        project_data={
            "name": "AI Productivity Suite Launch",
            "description": "Launch a new suite of AI productivity tools",
            "tasks": [
                {
                    "id": "task_001",
                    "type": "market_analysis",
                    "description": "Analyze the market for AI productivity tools",
                    "priority": "high"
                },
                {
                    "id": "task_002",
                    "type": "financial_analysis",
                    "description": "Create financial projections for the product",
                    "priority": "medium",
                    "dependencies": ["task_001"]
                },
                {
                    "id": "task_003",
                    "type": "content_creation",
                    "description": "Create marketing content for the launch",
                    "priority": "medium",
                    "dependencies": ["task_001"]
                }
            ],
            "agents": ["Marketing", "Finance", "Legal", "Strategy"]
        }
    )
    print(f"Project created: {project_result['id']}")
    print(f"Task assignments: {json.dumps(project_result['task_assignments'], indent=2)}")
    
    # Test resource conflict resolution
    print("\n=== Testing Resource Conflict Resolution ===")
    conflict_result = await manager.resolve_resource_conflict({
        "agents": ["Marketing", "Finance", "Legal"],
        "resource": "data_analysis_tool",
        "priority": {
            "Marketing": 2,
            "Finance": 3,
            "Legal": 1
        }
    })
    print(f"Resource conflict resolution: {json.dumps(conflict_result['allocation'], indent=2)}")
    
    # Test workflow optimization
    print("\n=== Testing Workflow Optimization ===")
    optimization_result = await manager.optimize_workflow_performance(
        workflow_id="workflow_001",
        performance_data={
            "task_durations": {
                "task_001": 120,
                "task_002": 300,  # Bottleneck
                "task_003": 150,
                "task_004": 90
            },
            "agent_performance": {
                "Marketing": {
                    "avg_duration": {"content_creation": 100},
                    "specializations": ["content_creation", "social_media"]
                },
                "Finance": {
                    "avg_duration": {"financial_analysis": 200},
                    "specializations": ["financial_analysis", "pricing_strategy"]
                },
                "Strategy": {
                    "avg_duration": {"market_analysis": 180},
                    "specializations": ["market_analysis", "competitive_analysis"]
                }
            },
            "task_assignments": {
                "task_001": "Strategy",
                "task_002": "Finance",
                "task_003": "Marketing",
                "task_004": "Marketing"
            },
            "task_types": {
                "task_001": "market_analysis",
                "task_002": "financial_analysis",
                "task_003": "content_creation",
                "task_004": "social_media"
            },
            "dependencies": {
                "task_001": ["task_002", "task_003"]
            }
        }
    )
    print(f"Bottlenecks identified: {len(optimization_result['bottlenecks'])}")
    print(f"Optimization recommendations: {json.dumps(optimization_result['recommendations'], indent=2)}")
    
    # Test knowledge coordination
    print("\n=== Testing Knowledge Coordination ===")
    coordination_result = await manager.coordinate_learning({
        "source_agent": "Marketing",
        "knowledge": {
            "type": "market_insight",
            "content": "AI productivity tools are most popular among tech startups and remote teams",
            "confidence": 0.85
        },
        "relevance": {
            "Marketing": 0.9,
            "Finance": 0.7,
            "Strategy": 0.8,
            "Legal": 0.3
        }
    })
    print(f"Knowledge shared with: {coordination_result['shared_with']}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_manager())