export interface User {
  id: string
  name: string
  email: string
  role: "admin" | "ceo"
  avatar?: string
}

export interface VirtualAgent {
  id: string
  name: string
  role: string
  status: "active" | "idle" | "working" | "waiting_approval"
  currentTask?: string
  avatar: string
  personality: string
  expertise: string[]
  workload: number
  performance: {
    tasksCompleted: number
    successRate: number
    avgResponseTime: string
  }
}

export interface Task {
  id: string
  title: string
  description: string
  assignedTo: string
  requestedBy: string
  status: "pending_approval" | "approved" | "in_progress" | "completed" | "rejected"
  priority: "low" | "medium" | "high" | "urgent"
  estimatedTime: string
  createdAt: string
  dueDate?: string
  approvalRequired: boolean
}

export interface Conversation {
  id: string
  participants: string[]
  messages: Message[]
  topic: string
  status: "active" | "archived"
}

export interface Message {
  id: string
  sender: string
  content: string
  timestamp: string
  type: "text" | "task_request" | "approval_request" | "system"
  metadata?: any
}

export interface BusinessPlan {
  id: string
  title: string
  description: string
  objectives: string[]
  timeline: string
  resources: string[]
  status: "draft" | "discussing" | "approved" | "executing"
  createdBy: string
  lastUpdated: string
}

// For components/ui/orchestration-board.tsx
// This will be derived from ActiveWorkflowRun (from types/workflow.ts)
// with some fields potentially mocked or generalized for now.
export interface TaskOrchestration {
  id: string; // thread_id from ActiveWorkflowRun
  title: string; // from input_data.title or workflow_name
  description: string; // from input_data.user_intent
  orchestratedBy: string; // This is tricky. For now, could be workflow_id or a generic "Manager Agent" ID.
                         // The backend ActiveWorkflowRun doesn't specify the orchestrator agent directly.
  startTime: string; // from started_at
  status: "executing" | "paused" | "completed" | "failed"; // Mapped from ActiveWorkflowRun status
  progress: number; // Mocked or calculated if possible. Default to 0 or 50 for running.
  parallelActions: Array<{ // Mocked for now, as this detail isn't in ActiveWorkflowRun
    id: string;
    action: string;
    agentId: string; // ID of the specialist agent performing action
    progress: number; // Progress of this specific action
    status: "pending" | "in_progress" | "completed" | "failed";
  }>;
  totalCost?: number; // Mocked
  estimatedCompletion?: string; // Mocked
  // Include the raw ActiveWorkflowRun for access to other fields if needed by handlers
  rawRunData?: import("./workflow").ActiveWorkflowRun;
}
