from typing import Any, Dict, List, Optional, Callable
import logging
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel

from ..models.workflow import AgentState, OrchestrationState
from ..services.qdrant_client import QdrantClient
from ..services.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class WorkflowConfig(BaseModel):
    """Configuration for a workflow"""
    name: str
    description: str
    agents: List[str]
    entry_point: str
    human_in_loop_points: List[str] = []
    max_iterations: int = 50

class LangGraphOrchestrator:
    def __init__(self, qdrant_client: Optional[QdrantClient] = None, neo4j_client: Optional[Neo4jClient] = None):
        self.qdrant_client = qdrant_client
        self.neo4j_client = neo4j_client
        self.workflows: Dict[str, StateGraph] = {}
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {} # thread_id -> run_info
        self.checkpointer = MemorySaver()
        self._register_default_workflows()

    def _register_default_workflows(self):
        """Registers pre-defined system workflows."""
        from ..api.agents import fixed_team_agents_data # Import here to avoid circular import issues at module level

        VIRTUAL_OFFICE_WORKFLOW_ID = "virtual_office_main_workflow_v1"
        if VIRTUAL_OFFICE_WORKFLOW_ID in self.workflows:
            logger.info(f"Default workflow {VIRTUAL_OFFICE_WORKFLOW_ID} already registered.")
            return

        cofounder_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
        manager_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))
        all_agent_ids = [agent_data['id'] for agent_data in fixed_team_agents_data]

        default_workflow_config_dict = {
            "name": "Virtual Office Main Workflow",
            "description": "Standard workflow for processing user intents with the virtual office team.",
            "agents": all_agent_ids,
            "entry_point": cofounder_agent_id,
            "human_in_loop_points": [], # Example: [manager_agent_id] for HIL after manager plans
            "max_iterations": 50
        }
        
        try:
            # This method is sync, so we call the synchronous parts of define_workflow.
            # Neo4j calls within define_workflow would need to be conditional or handled if this is called from sync context.
            # For now, assume define_workflow can handle this scenario or Neo4j part is omitted for this sync call.
            self.define_workflow_sync(default_workflow_config_dict, workflow_id_override=VIRTUAL_OFFICE_WORKFLOW_ID)
            logger.info(f"Default workflow '{default_workflow_config_dict['name']}' registered with ID: {VIRTUAL_OFFICE_WORKFLOW_ID}")
        except Exception as e:
            logger.error(f"Failed to register default workflow {VIRTUAL_OFFICE_WORKFLOW_ID}: {e}", exc_info=True)

    def define_workflow_sync(self, workflow_config: Dict[str, Any], workflow_id_override: Optional[str] = None):
        """Synchronous parts of defining a workflow. Neo4j operations should be handled carefully if called from sync context."""
        config = WorkflowConfig(**workflow_config)
        workflow_id = workflow_id_override if workflow_id_override else str(uuid.uuid4())

        if workflow_id in self.workflows:
            logger.warning(f"Workflow {workflow_id} already defined. Skipping re-definition.")
            return workflow_id

        workflow = StateGraph(OrchestrationState)
        for agent_id_node in config.agents: # Renamed to avoid conflict
            workflow.add_node(agent_id_node, self._create_agent_node(agent_id_node))

        cofounder_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
        manager_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))

        if config.entry_point == cofounder_agent_id and manager_agent_id in config.agents:
            workflow.add_edge(cofounder_agent_id, manager_agent_id)
            
            specialist_nodes = [aid for aid in config.agents if aid not in [cofounder_agent_id, manager_agent_id]]
            conditional_map_from_manager = {agent_id: agent_id for agent_id in specialist_nodes}
            conditional_map_from_manager[END] = END
            
            workflow.add_conditional_edges(
                manager_agent_id,
                self._route_from_manager,
                conditional_map_from_manager
            )
            for specialist_id in specialist_nodes:
                workflow.add_edge(specialist_id, END) # Simplified: specialist tasks end workflow
        else: # Generic definition
            workflow.add_conditional_edges(
                config.entry_point, self._route_to_next_agent,
                {agent_id: agent_id for agent_id in config.agents + [END]}
            )

        for hil_point in config.human_in_loop_points:
            if hil_point in config.agents:
                hil_node_name = f"{hil_point}_hil_check"
                workflow.add_node(hil_node_name, self._human_in_loop_node)
                # Basic: agent -> HIL check -> resume to same agent to re-evaluate or END. More complex routing needed.
                workflow.add_edge(hil_point, hil_node_name)
                workflow.add_edge(hil_node_name, END) # Placeholder for HIL resume logic

        workflow.set_entry_point(config.entry_point)
        compiled_workflow = workflow.compile(checkpointer=self.checkpointer)
        self.workflows[workflow_id] = compiled_workflow
        self.workflow_configs[workflow_id] = config

        # Neo4j part should ideally be async and called from an async context
        # For now, this synchronous version omits direct async Neo4j calls from here
        # Or assumes neo4j_client can handle being called from sync if it uses a sync driver part
        logger.info(f"Workflow '{config.name}' (ID: {workflow_id}) defined in memory.")
        # If self.neo4j_client.create_workflow_graph needs to be async, it can't be here directly.
        return workflow_id


    async def define_workflow(self, workflow_config: Dict[str, Any], workflow_id_override: Optional[str] = None) -> str:
        """Define a new workflow using LangGraph. workflow_id_override is for predefined workflows."""
        # This is the async wrapper that can include async DB calls.
        workflow_id = self.define_workflow_sync(workflow_config, workflow_id_override)
        config = self.workflow_configs[workflow_id]

        if self.neo4j_client:
            try:
                exists_query = "MATCH (w:Workflow {id: $workflow_id}) RETURN w IS NOT NULL AS exists"
                result = await self.neo4j_client.run_query(exists_query, {'workflow_id': workflow_id}) # run_query must be async
                if not (result and result[0]['exists']):
                    await self.neo4j_client.create_workflow_graph(workflow_id, { # create_workflow_graph must be async
                        'name': config.name, 'description': config.description,
                        'created_at': datetime.now().isoformat(), 'status': 'defined'
                    })
                    for agent_id_in_config in config.agents:
                        await self.neo4j_client.link_agent_to_workflow( # link_agent_to_workflow must be async
                            agent_id_in_config, workflow_id, 'participant'
                        )
                    logger.info(f"Workflow '{config.name}' (ID: {workflow_id}) graph data stored in Neo4j.")
            except Exception as e_neo:
                logger.error(f"Neo4j error during define_workflow for {workflow_id}: {e_neo}", exc_info=True)
        return workflow_id


    async def run_workflow(self, workflow_id: str, input_data: Dict[str, Any], config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a workflow with given input data"""
        if workflow_id not in self.workflows:
            # Attempt to define it if it's the default workflow and somehow not registered
            if workflow_id == "virtual_office_main_workflow_v1":
                logger.warning(f"Default workflow {workflow_id} not found during run, attempting to register.")
                try:
                    # This is tricky if run_workflow is async and _register_default_workflows calls sync define_workflow_sync
                    # For a robust solution, registration should happen reliably at startup in an async context.
                    self._register_default_workflows()
                except Exception as reg_err:
                     logger.error(f"Failed to auto-register default workflow {workflow_id} during run: {reg_err}")

                if workflow_id not in self.workflows: # Check again
                     raise ValueError(f"Default workflow {workflow_id} could not be registered or found.")
            else:
                raise ValueError(f"Workflow {workflow_id} not found")
        
        try:
            workflow_executable = self.workflows[workflow_id]
            thread_id = str(uuid.uuid4()) # Unique ID for this run

            user_intent_from_input = input_data.get('user_intent', input_data.get('description', 'No user intent provided'))

            initial_graph_state = OrchestrationState(
                user_request=user_intent_from_input,
                task_breakdown=[],
                assigned_agents=[],
                results={},
                coordination_messages=[HumanMessage(content=user_intent_from_input)],
                final_output=None
            )
            
            self.active_workflows[thread_id] = {
                'workflow_id': workflow_id,
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'input_data': input_data,
                'thread_id': thread_id
            }
            
            langgraph_config = {"configurable": {"thread_id": thread_id}}
            if config_override:
                langgraph_config.update(config_override)
            
            final_state_result = await workflow_executable.ainvoke(initial_graph_state.dict(), config=langgraph_config)
            
            self.active_workflows[thread_id]['status'] = 'completed' # Assuming it completes successfully
            self.active_workflows[thread_id]['completed_at'] = datetime.now().isoformat()
            self.active_workflows[thread_id]['result'] = final_state_result
            
            # Store results in memory systems
            if self.qdrant_client:
                await self._store_workflow_result_in_qdrant(workflow_id, thread_id, result)
            
            if self.neo4j_client:
                await self._store_workflow_result_in_neo4j(workflow_id, thread_id, result)
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return {
                'status': 'completed',
                'workflow_id': workflow_id,
                'thread_id': thread_id,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Failed to run workflow {workflow_id}: {e}")
            if thread_id in self.active_workflows:
                self.active_workflows[thread_id]['status'] = 'failed'
                self.active_workflows[thread_id]['error'] = str(e)
            raise

    async def get_workflow_state(self, workflow_id: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current state of a workflow"""
        if workflow_id not in self.workflows:
            return {'error': f'Workflow {workflow_id} not found'}
        
        try:
            if thread_id and thread_id in self.active_workflows:
                return self.active_workflows[thread_id]
            
            # Return general workflow info
            config = self.workflow_configs.get(workflow_id)
            return {
                'workflow_id': workflow_id,
                'name': config.name if config else 'Unknown',
                'status': 'defined',
                'agents': config.agents if config else [],
                'active_executions': [
                    exec_info for exec_info in self.active_workflows.values()
                    if exec_info['workflow_id'] == workflow_id
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            return {'error': str(e)}

    async def pause_workflow(self, thread_id: str) -> Dict[str, Any]:
        """Pause a running workflow"""
        if thread_id not in self.active_workflows:
            return {'error': f'Workflow thread {thread_id} not found'}
        
        try:
            self.active_workflows[thread_id]['status'] = 'paused'
            self.active_workflows[thread_id]['paused_at'] = datetime.now().isoformat()
            
            logger.info(f"Workflow thread {thread_id} paused")
            return {'status': 'paused', 'thread_id': thread_id}
            
        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            return {'error': str(e)}

    async def resume_workflow(self, thread_id: str, human_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resume a paused workflow"""
        if thread_id not in self.active_workflows:
            return {'error': f'Workflow thread {thread_id} not found'}
        
        try:
            workflow_info = self.active_workflows[thread_id]
            workflow_id = workflow_info['workflow_id']
            workflow = self.workflows[workflow_id]
            
            # Update status
            self.active_workflows[thread_id]['status'] = 'running'
            self.active_workflows[thread_id]['resumed_at'] = datetime.now().isoformat()
            
            if human_input:
                self.active_workflows[thread_id]['human_input'] = human_input
            
            logger.info(f"Workflow thread {thread_id} resumed")
            return {'status': 'resumed', 'thread_id': thread_id}
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return {'error': str(e)}

import asyncio # Required for asyncio.sleep

    def _create_agent_node(self, agent_id: str) -> Callable[[OrchestrationState], Dict[str, Any]]:
        """
        Creates a graph node function for a given agent.
        Returns a dictionary of fields to update in the OrchestrationState.
        """
        async def agent_node_wrapper(state: OrchestrationState) -> Dict[str, Any]:
            logger.info(f"--- Orchestrator: Agent Node: {agent_id} ---")
            await asyncio.sleep(0.1) # Simulate async work

            # Placeholder: actual agent logic would go here
            agent_output = f"Output from {agent_id} for request: {state.user_request[:20]}..."

            # Update results and messages
            updated_results = state.results.copy()
            updated_results[agent_id] = {"status": "completed", "output": agent_output, "timestamp": datetime.now().isoformat()}

            new_coordination_messages = state.coordination_messages + [
                AIMessage(content=f"Agent {agent_id} processed. Output: {agent_output}")
            ]

            updated_assigned_agents = list(set(state.assigned_agents + [agent_id]))

            # This dictionary will be used to update the overall OrchestrationState
            return {
                "results": updated_results,
                "coordination_messages": new_coordination_messages,
                "assigned_agents": updated_assigned_agents
            }
        return agent_node_wrapper

    def _route_to_next_agent(self, state: OrchestrationState) -> str: # Generic router
        """Generic router, determines the next agent or END."""
        # This is a placeholder. A real router would be more complex.
        logger.debug(f"Generic router: current assigned_agents: {state.assigned_agents}, routing to END.")
        return END

    def _route_from_manager(self, state: OrchestrationState) -> str:
        """Routing logic after the Manager agent node."""
        manager_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))
        manager_results = state.results.get(manager_agent_id, {})
        manager_output = manager_results.get("output", "")

        logger.info(f"Manager output for routing: '{manager_output}'")
        # Placeholder: if manager mentions "CRM", route to CRM agent, else END.
        # A real implementation would parse a structured plan from the manager.
        crm_agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000003"))
        if "crm" in manager_output.lower() and crm_agent_id not in state.assigned_agents: # Avoid re-running
            logger.info("Manager routing to CRM Agent.")
            return crm_agent_id
        
        logger.info("Manager routing to END.")
        return END

    async def _human_in_loop_node(self, state: OrchestrationState) -> Dict[str, Any]:
        """Handles a human-in-the-loop checkpoint."""
        logger.info(f"--- Orchestrator: HIL Node reached for request: {state.user_request[:50]}... ---")
        # This node prepares state for HIL. Actual pausing is via LangGraph interrupt.
        hil_message = AIMessage(content="Human input required to proceed.")
        return {
            "coordination_messages": state.coordination_messages + [hil_message],
            "waiting_for_hil": True # Flag for UI or other systems
        }

    async def _store_workflow_result_in_qdrant(self, workflow_id: str, thread_id: str, result: Dict[str, Any]):
        """Store workflow results in Qdrant for semantic search"""
        try:
            # Create embeddings for the workflow result
            # This would use your embedding service
            collection_name = f"workflow_results"
            
            vector_data = {
                'id': thread_id,
                'vector': [0.0] * 1536,  # Placeholder - use actual embeddings
                'payload': {
                    'workflow_id': workflow_id,
                    'thread_id': thread_id,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            await self.qdrant_client.create_collection(collection_name)
            await self.qdrant_client.upsert_vectors(collection_name, [vector_data])
            
        except Exception as e:
            logger.error(f"Failed to store workflow result in Qdrant: {e}")

    async def _store_workflow_result_in_neo4j(self, workflow_id: str, thread_id: str, result: Dict[str, Any]):
        """Store workflow results in Neo4j for graph relationships"""
        try:
            # Create execution node
            execution_data = {
                'thread_id': thread_id,
                'status': 'completed',
                'result': result,
                'completed_at': datetime.now().isoformat()
            }
            
            query = """
            MATCH (w:Workflow {id: $workflow_id})
            CREATE (e:Execution {
                id: $thread_id,
                status: $status,
                completed_at: $completed_at
            })
            CREATE (w)-[:HAS_EXECUTION]->(e)
            RETURN e
            """
            
            await self.neo4j_client.run_query(query, {
                'workflow_id': workflow_id,
                'thread_id': thread_id,
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to store workflow result in Neo4j: {e}")

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all defined workflows"""
        workflows = []
        for workflow_id, config in self.workflow_configs.items():
            workflows.append({
                'id': workflow_id,
                'name': config.name,
                'description': config.description,
                'agents': config.agents,
                'status': 'defined'
            })
        return workflows

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
            if workflow_id in self.workflow_configs:
                del self.workflow_configs[workflow_id]
            
            # Remove from Neo4j if available
            if self.neo4j_client:
                query = "MATCH (w:Workflow {id: $workflow_id}) DETACH DELETE w"
                await self.neo4j_client.run_query(query, {'workflow_id': workflow_id})
            
            logger.info(f"Workflow {workflow_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False

    async def list_active_workflow_runs(self, workflow_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all active (running or paused) workflow runs, optionally filtered by workflow_id."""
        active_runs = []
        for thread_id, run_info in self.active_workflows.items():
            if run_info.get('status') in ['running', 'paused']:
                if workflow_id_filter and run_info.get('workflow_id') != workflow_id_filter:
                    continue
                # Add workflow name to the run info for better context
                run_info_enriched = run_info.copy()
                workflow_config = self.workflow_configs.get(run_info.get('workflow_id'))
                run_info_enriched['workflow_name'] = workflow_config.name if workflow_config else 'Unknown Workflow'
                active_runs.append(run_info_enriched)
        return active_runs