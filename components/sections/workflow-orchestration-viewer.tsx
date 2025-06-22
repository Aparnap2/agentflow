"use client"

import { useState, useEffect } from "react"
import { OrchestrationBoard } from "@/components/ui/orchestration-board"
import type { TaskOrchestration, VirtualAgent } from "@/types/virtual-office"
import type { ActiveWorkflowRun } from "@/types/workflow"
import { useToast } from "@/hooks/use-toast"
import { AlertTriangle, Loader2 } from "lucide-react"

// Helper to map ActiveWorkflowRun to frontend TaskOrchestration type
const mapActiveRunToTaskOrchestration = (run: ActiveWorkflowRun): TaskOrchestration => {
  let status: TaskOrchestration["status"] = "executing"; // Default
  if (run.status === "paused") status = "paused";
  else if (run.status === "completed") status = "completed";
  else if (run.status === "failed") status = "failed";
  else if (run.status === "running") status = "executing";

  // Mocked progress and parallel actions for now
  let progress = 0;
  if (status === "completed") progress = 100;
  else if (status === "executing" || status === "paused") progress = Math.floor(Math.random() * 70) + 10; // Random progress for demo

  return {
    id: run.thread_id,
    title: run.input_data?.title || run.workflow_name || "Workflow Run",
    description: run.input_data?.user_intent || run.input_data?.description || "No description available.",
    // For now, use a placeholder for orchestratedBy. This should ideally be the Manager agent's ID.
    // Or, if the workflow definition has a designated orchestrator agent.
    orchestratedBy: run.workflow_id, // Using workflow_id as a stand-in, needs refinement
    startTime: run.started_at,
    status: status,
    progress: progress,
    parallelActions: status === "executing" || status === "paused" ? [
      // Mock one or two parallel actions for display
      { id: "action1-" + run.thread_id, action: "Gathering initial data", agentId: "crm-specialist-id-placeholder", progress: Math.floor(Math.random() * 100), status: "in_progress" },
      { id: "action2-" + run.thread_id, action: "Drafting communication", agentId: "email-specialist-id-placeholder", progress: Math.floor(Math.random() * 30), status: "pending" }
    ] : [],
    totalCost: Math.random() * 10, // Mocked
    estimatedCompletion: status !== "completed" && status !== "failed" ?
        new Date(Date.now() + Math.random() * 3600000 * 2).toISOString() : undefined, // Mocked
    rawRunData: run, // Keep original data
  };
};

interface WorkflowOrchestrationViewerProps {
  agents: VirtualAgent[]; // Pass down the list of known agents for avatar mapping etc.
}

export function WorkflowOrchestrationViewer({ agents }: WorkflowOrchestrationViewerProps) {
  const [orchestrations, setOrchestrations] = useState<TaskOrchestration[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const VIRTUAL_OFFICE_WORKFLOW_ID = "virtual_office_main_workflow_v1";

  const fetchOrchestrations = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/workflows/runs/active?workflow_id=${VIRTUAL_OFFICE_WORKFLOW_ID}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch orchestrations: ${response.status} ${response.statusText}`)
      }
      const data: { active_runs: ActiveWorkflowRun[] } = await response.json()
      setOrchestrations(data.active_runs.map(mapActiveRunToTaskOrchestration))
    } catch (err) {
      console.error("Error fetching orchestrations:", err)
      setError(err instanceof Error ? err.message : "An unknown error occurred")
      toast({ title: "Error", description: "Could not fetch workflow orchestrations.", variant: "destructive"})
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchOrchestrations()
    // Optional: Set up polling if real-time updates are desired without WebSockets yet
    // const intervalId = setInterval(fetchOrchestrations, 30000); // Poll every 30 seconds
    // return () => clearInterval(intervalId);
  }, [])

  const handlePauseOrchestration = async (threadId: string) => {
    const run = orchestrations.find(o => o.id === threadId)?.rawRunData;
    if (!run) return;
    try {
      const response = await fetch(`/api/workflows/${run.workflow_id}/runs/${threadId}/pause`, { method: "POST" });
      if (!response.ok) throw new Error("Failed to pause orchestration");
      toast({ title: "Orchestration Paused", description: `Workflow ${threadId} paused.` });
      fetchOrchestrations(); // Refresh list
    } catch (err) {
      toast({ title: "Error", description: (err as Error).message, variant: "destructive" });
    }
  };

  const handleResumeOrchestration = async (threadId: string) => {
     const run = orchestrations.find(o => o.id === threadId)?.rawRunData;
    if (!run) return;
    try {
      // Simple resume, no specific human_input here. This could be expanded.
      const response = await fetch(`/api/workflows/${run.workflow_id}/runs/${threadId}/resume`, { method: "POST" });
      if (!response.ok) throw new Error("Failed to resume orchestration");
      toast({ title: "Orchestration Resumed", description: `Workflow ${threadId} resumed.` });
      fetchOrchestrations(); // Refresh list
    } catch (err) {
      toast({ title: "Error", description: (err as Error).message, variant: "destructive" });
    }
  };

  const handleCancelOrchestration = async (threadId: string) => {
    // TODO: Implement cancellation. This might involve a new backend endpoint or a specific state update.
    // For now, it could be a "soft" cancel (mark as failed/cancelled locally or via a generic update if possible)
    toast({ title: "Action Needed", description: `Cancellation for ${threadId} not yet implemented.`, variant: "default" });
    console.warn(`Cancellation requested for ${threadId} - not implemented yet.`);
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-muted-foreground">Loading Workflow Runs...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="my-4 rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-700 dark:bg-red-900/30">
        <div className="flex items-center">
          <AlertTriangle className="h-6 w-6 text-red-500" />
          <h3 className="ml-2 text-lg font-semibold text-red-700 dark:text-red-300">Failed to load workflow runs</h3>
        </div>
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
      </div>
    )
  }

  if (orchestrations.length === 0) {
    return (
        <div className="py-8 text-center">
            <h3 className="text-xl font-semibold">No Active Workflow Runs</h3>
            <p className="text-muted-foreground">Submit a new task to see it orchestrated here.</p>
        </div>
    )
  }

  return (
    <div className="mt-8">
        <h2 className="mb-4 text-2xl font-bold">Active Workflow Orchestrations</h2>
        <OrchestrationBoard
            orchestrations={orchestrations}
            agents={agents}
            onPauseOrchestration={handlePauseOrchestration}
            onResumeOrchestration={handleResumeOrchestration}
            onCancelOrchestration={handleCancelOrchestration}
        />
    </div>
  )
}
