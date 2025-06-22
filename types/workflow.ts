// Represents an active workflow run/instance from the backend
// Based on the structure likely from orchestrator.active_workflows
export interface ActiveWorkflowRun {
  thread_id: string;
  workflow_id: string; // Definition ID (e.g., "virtual_office_main_workflow_v1")
  workflow_name: string; // Name of the workflow definition
  status: "running" | "paused" | "completed" | "failed"; // Backend status
  started_at: string; // ISO datetime string
  input_data?: {
    user_intent?: string;
    title?: string;
    description?: string;
    [key: string]: any; // Other input data
  };
  // Optional fields that might be present depending on the state
  error?: string;
  result?: any;
  paused_at?: string;
  resumed_at?: string;
  completed_at?: string;
  human_input?: any;
  // We might add more details here as we find out what get_workflow_state(thread_id) returns
  // For example, current_step, agent_states, messages etc.
}

// For defining a new workflow (currently used by POST /api/workflows)
// Matches backend WorkflowCreateRequest
export interface WorkflowCreateRequest {
  name: str;
  description: str;
  agents: string[];
  entry_point: str;
  human_in_loop_points?: string[];
  max_iterations?: number;
}

// For submitting a new user task (intent)
// Matches backend UserTaskRequest (POST /api/workflows/submit-task)
export interface UserTaskRequest {
  user_intent: string;
  name?: string;
  description?: string;
}

// Expected response from POST /api/workflows/submit-task
// Matches backend response structure
export interface UserTaskResponse {
    message: string;
    workflow_id: string; // Definition ID (e.g., "virtual_office_main_workflow_v1")
    run_details: { // This structure depends on orchestrator.run_workflow actual return
        thread_id?: string; // This is the crucial ID for the run
        run_id?: string;
        id?: string;
        status?: string;
        [key: string]: any; // Other details from the run
    };
}

// General Workflow Definition (from GET /api/workflows)
// Matches structure from orchestrator.list_workflows()
export interface WorkflowDefinitionInfo {
  id: string;
  name: string;
  description: string;
  agents: string[];
  status: 'defined';
}

// For HIL (Human In Loop) requests and responses
// Based on backend HILRequestCreate and HILResponseSubmit
export enum HILStatus {
  APPROVED = "approved",
  REJECTED = "rejected",
  MORE_INFO_REQUESTED = "more_info_requested",
  // Add other statuses as needed
}

export interface HILRequest {
    id: string; // request_id
    workflow_id: string;
    thread_id: string;
    agent_id: string;
    request_type: string;
    title: string;
    description: string;
    context: Record<string, any>;
    proposed_action?: Record<string, any>;
    options?: Array<Record<string, any>>;
    priority: string;
    status: "pending" | "responded" | "expired"; // HIL service internal status
    created_at: string;
    responded_at?: string;
    timeout_at?: string;
}

export interface HILResponseSubmitPayload {
    status: HILStatus;
    response_data?: Record<string, any>;
    comments?: string;
    responded_by?: string; // Default "human"
}
