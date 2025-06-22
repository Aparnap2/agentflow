"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { ChatInterface } from "@/components/ui/chat-interface"
import { VirtualTeamPanel } from "@/components/ui/virtual-team-panel"
import { ApprovalQueue } from "@/components/ui/approval-queue"
import { StatCard } from "@/components/ui/stat-card"
import { Users, CheckCircle, Clock, TrendingUp, AlertTriangle } from "lucide-react"
import type { VirtualAgent, Task, Message } from "@/types/virtual-office"
// AgentConfig is no longer fetched here, but VirtualAgent type is used for props
// import type { AgentConfig } from "@/types/agent"
import type { ActiveWorkflowRun } from "@/types/workflow"
import { useToast } from "@/hooks/use-toast";


// mapAgentConfigToVirtualAgent is now in EnhancedVirtualOffice.tsx

// Helper to map ActiveWorkflowRun to frontend Task type
const mapActiveRunToTask = (run: ActiveWorkflowRun): Task => {
  let taskStatus: Task["status"] = "in_progress"; // Default
  if (run.status === "paused") {
    // This is a simple mapping. Real "pending_approval" would come from HIL state.
    // For now, let's assume paused might mean it's awaiting something.
    taskStatus = "pending_approval";
  } else if (run.status === "completed") {
    taskStatus = "completed";
  } else if (run.status === "failed") {
    taskStatus = "failed";
  } else if (run.status === "running") {
    taskStatus = "in_progress";
  }

  return {
    id: run.thread_id,
    title: run.input_data?.title || run.workflow_name || "Workflow Run",
    description: run.input_data?.user_intent || run.input_data?.description || "No description",
    // assignedTo, requestedBy, priority, estimatedTime are not directly available from ActiveWorkflowRun
    // These would require more detailed state from the workflow instance or HIL system
    status: taskStatus,
    createdAt: run.started_at,
    approvalRequired: taskStatus === "pending_approval", // Basic assumption
  };
};

// Mock data for chat messages - will be replaced in later steps
const chatMessages: Message[] = [
  {
    id: "1",
    sender: "Alex Chen",
    content:
      "Good morning! I've been analyzing our Q1 performance. We should focus on automating our lead qualification process to improve conversion rates.",
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    type: "text",
  },
  {
    id: "2",
    sender: "You",
    content: "That sounds great, Alex. What's your recommendation for the implementation approach?",
    timestamp: new Date(Date.now() - 7000000).toISOString(),
    type: "text",
  },
  {
    id: "3",
    sender: "Alex Chen",
    content:
      "I suggest we start with CRM automation and email marketing integration. Sarah can coordinate the team to implement this in phases.",
    timestamp: new Date(Date.now() - 6800000).toISOString(),
    type: "text",
  },
  {
    id: "4",
    sender: "Sarah Kim",
    content:
      "I'd like to assign the lead scoring system to Mike and the email sequences to Emma. May I have your approval to proceed?",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    type: "approval_request",
    metadata: { taskId: "task-1" },
  },
]

export function VirtualOfficeDashboard() {
interface VirtualOfficeDashboardProps {
  teamMembers: VirtualAgent[];
}

export function VirtualOfficeDashboard({ teamMembers }: VirtualOfficeDashboardProps) {
  // teamMembers is now passed as a prop.
  // isLoadingTeam and errorLoadingTeam are handled by the parent (EnhancedVirtualOffice)

  const [activeWorkflowsAsTasks, setActiveWorkflowsAsTasks] = useState<Task[]>([])
  const [isLoadingTasks, setIsLoadingTasks] = useState(true)
  const [errorLoadingTasks, setErrorLoadingTasks] = useState<string | null>(null)

  const [messages, setMessages] = useState<Message[]>(chatMessages)

  useEffect(() => {
    const fetchActiveTasks = async () => {
      setIsLoadingTasks(true)
      setErrorLoadingTasks(null)
      try {
        const tasksResponse = await fetch("http://localhost:8000/api/workflows/runs/active?workflow_id=virtual_office_main_workflow_v1")
        if (!tasksResponse.ok) {
          throw new Error(`Failed to fetch active tasks: ${tasksResponse.status} ${tasksResponse.statusText}`)
        }
        const tasksData: { active_runs: ActiveWorkflowRun[] } = await tasksResponse.json()
        setActiveWorkflowsAsTasks(tasksData.active_runs.map(mapActiveRunToTask))
      } catch (error) {
        console.error("Error fetching active tasks:", error)
        setErrorLoadingTasks(error instanceof Error ? error.message : "An unknown error occurred")
      } finally {
        setIsLoadingTasks(false)
      }
    };

    fetchActiveTasks()
  }, []) // Runs once on mount, or could be triggered by a refresh mechanism

  const handleSendMessage = (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      sender: "You",
      content,
      timestamp: new Date().toISOString(),
      type: "text",
    }
    setMessages((prev) => [...prev, newMessage])
  }

  const { toast } = useToast(); // Assuming useToast is imported

  const handleApproveTask = async (threadId: string) => {
    // This is a simplified call to the generic resume endpoint.
    // Proper HIL would use dedicated HIL response endpoints and include HIL request IDs.
    try {
      const workflowDefinitionId = "virtual_office_main_workflow_v1"; // This context might still be useful
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowDefinitionId}/runs/${threadId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ human_input: { approved: true, comment: "Approved via UI from dashboard" } }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to approve task: ${response.status}`);
      }

      const result = await response.json();
      toast({ title: "Task Approved", description: `Task ${threadId} resumed.` });

      // Refresh task list or update local state
      setActiveWorkflowsAsTasks((prevTasks) =>
        prevTasks.map((task) => (task.id === threadId ? { ...task, status: "in_progress" } : task))
      );
      // Add a message to chat history
      const taskTitle = activeWorkflowsAsTasks.find((t) => t.id === threadId)?.title || "Task";
      const approvalMessage: Message = {
        id: Date.now().toString(), sender: "You", content: `Approved: ${taskTitle}`,
        timestamp: new Date().toISOString(), type: "text",
      };
      setMessages((prev) => [...prev, approvalMessage]);

    } catch (error) {
      console.error("Error approving task:", error);
      toast({ title: "Error", description: error instanceof Error ? error.message : "Could not approve task.", variant: "destructive" });
    }
  };

  const handleRejectTask = async (threadId: string) => {
    // Simplified: For now, "rejecting" might mean just commenting or providing feedback.
    // A true HIL reject might involve a different status or payload.
    // This example just sends a comment, but the workflow itself might not use this "rejection" to stop.
    // It might be better to call a /pause or specific /reject HIL endpoint if available.
    // For now, let's simulate it by sending a "rejected" input, and locally setting to paused.
    // A more robust solution might involve a different endpoint or payload for explicit rejection if the backend workflow handles it.
    // Alternatively, this could call the PAUSE endpoint if "reject" means "pause for more info".
     try {
      const workflowDefinitionId = "virtual_office_main_workflow_v1";
      // For "reject", we are still calling "resume" but with different input.
      // The backend LangGraph graph would need to interpret this input.
      // If "reject" truly means "stop and mark as failed/rejected", a different endpoint or HIL flow is better.
      // For now, this sends a "rejected" human_input to the resume endpoint.
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowDefinitionId}/runs/${threadId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ human_input: { approved: false, comment: "Rejected via UI from dashboard" } }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to action task: ${response.status}`);
      }

      toast({ title: "Task Actioned (Rejected)", description: `Feedback sent for task ${threadId}.` });

      setActiveWorkflowsAsTasks((prevTasks) =>
        prevTasks.map((task) => (task.id === threadId ? { ...task, status: "paused" } : task)) // Visually show as paused
      );
      const taskTitle = activeWorkflowsAsTasks.find((t) => t.id === threadId)?.title || "Task";
      const rejectionMessage: Message = {
        id: Date.now().toString(), sender: "You", content: `Rejected: ${taskTitle}. Awaiting review or further changes.`,
        timestamp: new Date().toISOString(), type: "text",
      };
      setMessages((prev) => [...prev, rejectionMessage]);

    } catch (error) {
      console.error("Error rejecting task:", error);
      toast({ title: "Error", description: error instanceof Error ? error.message : "Could not action task.", variant: "destructive" });
    }
  };

  // Calculate stats based on fetched teamMembers
  const activeAgentsCount = teamMembers.filter((a) => a.status === "active" || a.status === "working").length
  const totalTasksCompleted = teamMembers.reduce((sum, agent) => sum + (agent.performance?.tasksCompleted || 0), 0)
  const avgSuccessRate = teamMembers.length > 0
    ? Math.round(teamMembers.reduce((sum, agent) => sum + (agent.performance?.successRate || 0), 0) / teamMembers.length)
    : 0

  const pendingApprovalCount = activeWorkflowsAsTasks.filter(task => task.status === "pending_approval").length;

  // Loading and error states for tasks are now handled here.
  // Team loading/error is handled by parent.
  if (isLoadingTasks) {
    return (
      <div className="flex justify-center items-center h-64">
        <Users className="w-12 h-12 animate-spin text-blue-500" /> {/* Changed color slightly */}
        <p className="ml-4 text-lg text-muted-foreground">Loading Active Tasks...</p>
      </div>
    );
  }

  if (errorLoadingTasks) {
    return (
      <div className="my-4 flex flex-col justify-center items-center bg-red-50 dark:bg-red-900/30 p-6 rounded-lg border border-red-200 dark:border-red-700">
        <AlertTriangle className="w-12 h-12 text-red-500" />
        <p className="mt-4 text-lg font-semibold text-red-700 dark:text-red-300">Error Loading Tasks</p>
        <p className="text-sm text-red-600 dark:text-red-400">{errorLoadingTasks}</p>
        <p className="text-xs text-muted-foreground mt-2">Ensure the workflow API is running.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Virtual Office Dashboard</h2>
          <p className="text-muted-foreground">Command and monitor your AI-powered virtual team</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 px-3 py-1">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            {activeAgentsCount} Active
          </Badge>
          <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200 px-3 py-1">
            <Clock className="w-3 h-3 mr-1" />
            {pendingApprovalCount} Pending
          </Badge>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Team Members"
          value={activeAgentsCount}
          description="AI agents available"
          icon={Users}
          color="blue"
        />
        <StatCard
          title="Pending Approvals"
          value={pendingApprovalCount}
          description="Tasks awaiting approval"
          icon={Clock}
          color="orange"
        />
        <StatCard
          title="Tasks Completed (Team)" // Updated to reflect team total
          value={totalTasksCompleted} // This stat is from agent performance, not directly from active workflows
          description="Total team output"
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Avg. Success Rate (Team)" // Updated to reflect team average
          value={`${avgSuccessRate}%`} // This stat is from agent performance
          description="Team performance"
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <ChatInterface
            participants={teamMembers} // Use fetched team members
            messages={messages}
            onSendMessage={handleSendMessage}
            onApproveTask={handleApproveTask}
            onRejectTask={handleRejectTask}
          />
        </div>

        {/* Team Panel */}
        <div>
          <VirtualTeamPanel agents={teamMembers} /> {/* Use fetched team members */}
        </div>
      </div>

      {/* Approval Queue */}
      <ApprovalQueue tasks={activeWorkflowsAsTasks} agents={teamMembers} onApprove={handleApproveTask} onReject={handleRejectTask} />
    </div>
  )
}
