"""
Initialization script for LangGraph system
"""
import asyncio
from loguru import logger
from dotenv import load_dotenv

from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from core.agent_factory import AgentFactory
from events.event_bus import event_bus

# Load environment variables
load_dotenv()

async def init_langgraph():
    """Initialize LangGraph system"""
    logger.debug("Initializing LangGraph system")
    
    # Initialize components
    memory_manager = MemoryManager()
    approval_manager = ApprovalManager()
    
    # Initialize agent factory
    factory = AgentFactory(memory_manager, approval_manager)
    
    # Set up event listeners
    await event_bus.subscribe("workflow_created", _on_workflow_created)
    await event_bus.subscribe("workflow_completed", _on_workflow_completed)
    await event_bus.subscribe("workflow_error", _on_workflow_error)
    
    logger.debug("LangGraph system initialized")
    return factory

async def _on_workflow_created(event_type, data):
    """Handle workflow created event"""
    workflow_id = data.get("workflow_id")
    logger.info(f"Workflow created: {workflow_id}")

async def _on_workflow_completed(event_type, data):
    """Handle workflow completed event"""
    workflow_id = data.get("workflow_id")
    agents_completed = data.get("agents_completed", [])
    logger.info(f"Workflow {workflow_id} completed with {len(agents_completed)} agents")

async def _on_workflow_error(event_type, data):
    """Handle workflow error event"""
    workflow_id = data.get("workflow_id")
    error = data.get("error")
    logger.error(f"Workflow {workflow_id} failed: {error}")

# Lazy initialization
factory = None

async def get_factory():
    """Get or initialize factory"""
    global factory
    if factory is None:
        factory = await init_langgraph()
    return factory