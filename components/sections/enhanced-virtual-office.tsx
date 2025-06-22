"use client"

import { useState, useEffect } from "react"
import { VirtualOfficeDashboard } from "./virtual-office-dashboard"
import { WorkflowOrchestrationViewer } from "./workflow-orchestration-viewer"
import type { VirtualAgent } from "@/types/virtual-office"
import type { AgentConfig } from "@/types/agent"
import { Users, AlertTriangle, Loader2 } from "lucide-react" // Added Loader2

// Helper to map backend AgentConfig to frontend VirtualAgent (can be moved to a utils file if not already)
const mapAgentConfigToVirtualAgent = (agentConfig: AgentConfig): VirtualAgent => {
  const status: VirtualAgent["status"] = agentConfig.is_active ? "active" : "idle";
  const performance = {
    tasksCompleted: agentConfig.performance_metrics?.tasks_completed || 0,
    successRate: agentConfig.performance_metrics?.success_rate || 0,
    avgResponseTime: agentConfig.performance_metrics?.avg_response_time || "N/A",
  };
  return {
    id: agentConfig.id,
    name: agentConfig.name,
    role: agentConfig.role.toString().replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
    status: status,
    avatar: `/placeholder.svg?seed=${agentConfig.id}`, // Generic placeholder
    expertise: agentConfig.specializations || [],
    personality: "N/A", // Placeholder - not in backend AgentConfig
    workload: 50, // Placeholder - not in backend AgentConfig
    currentTask: status === "working" ? "Processing tasks..." : undefined, // Placeholder
    performance: performance,
  };
};

export function EnhancedVirtualOffice() {
  const [teamMembers, setTeamMembers] = useState<VirtualAgent[]>([])
  const [isLoadingTeam, setIsLoadingTeam] = useState(true)
  const [errorLoadingTeam, setErrorLoadingTeam] = useState<string | null>(null)

  useEffect(() => {
    const fetchTeamMembers = async () => {
      setIsLoadingTeam(true)
      setErrorLoadingTeam(null)
      try {
        const teamResponse = await fetch("http://localhost:8000/api/agents/team-definition")
        if (!teamResponse.ok) {
          throw new Error(`Failed to fetch team members: ${teamResponse.status} ${teamResponse.statusText}`)
        }
        const teamData: AgentConfig[] = await teamResponse.json()
        setTeamMembers(teamData.map(mapAgentConfigToVirtualAgent))
      } catch (error) {
        console.error("Error fetching team members:", error)
        setErrorLoadingTeam(error instanceof Error ? error.message : "An unknown error occurred")
      } finally {
        setIsLoadingTeam(false)
      }
    };
    fetchTeamMembers()
  }, [])

  if (isLoadingTeam) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <Loader2 className="w-12 h-12 animate-spin text-blue-600" />
        <p className="ml-4 text-lg text-muted-foreground">Loading Virtual Office Team...</p>
      </div>
    );
  }

  if (errorLoadingTeam) {
    return (
      <div className="my-8 flex flex-col justify-center items-center bg-red-50 dark:bg-red-900/30 p-6 rounded-lg border border-red-200 dark:border-red-700">
        <AlertTriangle className="w-12 h-12 text-red-500" />
        <p className="mt-4 text-lg font-semibold text-red-700 dark:text-red-300">Error Loading Team</p>
        <p className="text-sm text-red-600 dark:text-red-400">{errorLoadingTeam}</p>
        <p className="text-xs text-muted-foreground mt-2">Please ensure the backend API for team definition is running and accessible.</p>
      </div>
    );
  }

  // Render dashboard and orchestration viewer only if team members are loaded successfully
  if (teamMembers.length === 0 && !isLoadingTeam && !errorLoadingTeam) {
    return (
         <div className="my-8 flex flex-col justify-center items-center p-6 rounded-lg border">
            <Users className="w-12 h-12 text-muted-foreground" />
            <p className="mt-4 text-lg font-semibold">No Team Members Found</p>
            <p className="text-sm text-muted-foreground">The virtual office team could not be loaded.</p>
        </div>
    )
  }

  return (
    <div className="space-y-8">
      <VirtualOfficeDashboard teamMembers={teamMembers} />
      <WorkflowOrchestrationViewer agents={teamMembers} />
    </div>
  )
}
