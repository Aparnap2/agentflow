import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

// Enhanced workflow context with personality-driven agent system
const WorkflowContext = createContext()

export const useWorkflow = () => {
  const context = useContext(WorkflowContext)
  if (!context) {
    throw new Error('useWorkflow must be used within WorkflowProvider')
  }
  return context
}

export const WorkflowProvider = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  
  // Enhanced workflow state with agent personalities
  const [workflowState, setWorkflowState] = useState({
    // Core workflow state
    currentPhase: 'introduction',
    conversationId: null,
    projectId: null,
    projectVision: '',
    userName: '',
    
    // Agent collaboration state
    activeAgent: 'Cofounder',
    agentConversations: {},
    agentProgress: {},
    
    // Approval state
    pendingApprovals: [],
    visionApproved: false,
    tasksDistributed: false,
    
    // Output state
    generatedOutputs: {},
    outputsReady: false,
    
    // UI state
    showAgentTransition: false,
    transitionAgent: null,
    showSidebar: true,
    
    // WebSocket state
    connected: false,
    lastUpdate: null
  })
  
  // Workflow phases define the user journey
  const workflowPhases = {
    introduction: {
      path: '/',
      next: 'vision',
      canSkip: false,
      requiredState: null
    },
    vision: {
      path: '/conversation',
      next: 'planning',
      canSkip: false,
      requiredState: null
    },
    planning: {
      path: '/planning',
      next: 'execution',
      canSkip: false,
      requiredState: 'visionApproved'
    },
    execution: {
      path: '/execution',
      next: 'results',
      canSkip: false,
      requiredState: 'tasksDistributed'
    },
    results: {
      path: '/results',
      next: 'dashboard',
      canSkip: false,
      requiredState: 'outputsReady'
    },
    dashboard: {
      path: '/dashboard',
      next: null,
      canSkip: false,
      requiredState: 'outputsReady'
    }
  }
  
  // Update workflow state with new values
  const updateWorkflowState = (updates) => {
    setWorkflowState(prev => ({ ...prev, ...updates }))
  }
  
  // Navigate to a specific phase
  const navigateToPhase = (phase) => {
    const phaseConfig = workflowPhases[phase]
    if (!phaseConfig) return
    
    // Check if required state is met
    if (phaseConfig.requiredState && !workflowState[phaseConfig.requiredState]) {
      // Find the furthest allowed phase
      const allowedPhases = Object.entries(workflowPhases)
        .filter(([_, config]) => !config.requiredState || workflowState[config.requiredState])
        .map(([phase]) => phase)
      
      const furthestPhase = allowedPhases[allowedPhases.length - 1]
      setWorkflowState(prev => ({ ...prev, currentPhase: furthestPhase }))
      navigate(workflowPhases[furthestPhase].path)
      return
    }
    
    setWorkflowState(prev => ({ ...prev, currentPhase: phase }))
    navigate(phaseConfig.path)
  }
  
  // Move to the next phase in the workflow
  const nextPhase = () => {
    const currentPhaseConfig = workflowPhases[workflowState.currentPhase]
    if (currentPhaseConfig?.next) {
      navigateToPhase(currentPhaseConfig.next)
    }
  }
  
  // Transition to a different agent with animation
  const transitionToAgent = (agentName) => {
    setWorkflowState(prev => ({
      ...prev,
      showAgentTransition: true,
      transitionAgent: agentName
    }))
    
    // After animation completes, update active agent
    setTimeout(() => {
      setWorkflowState(prev => ({
        ...prev,
        activeAgent: agentName,
        showAgentTransition: false
      }))
    }, 1000)
  }
  
  // Update agent progress
  const updateAgentProgress = (agentName, progress) => {
    setWorkflowState(prev => ({
      ...prev,
      agentProgress: {
        ...prev.agentProgress,
        [agentName]: progress
      }
    }))
  }
  
  // Store conversation with an agent
  const storeAgentConversation = (agentName, messages) => {
    setWorkflowState(prev => ({
      ...prev,
      agentConversations: {
        ...prev.agentConversations,
        [agentName]: messages
      }
    }))
  }
  
  // Add a pending approval
  const addPendingApproval = (approval) => {
    setWorkflowState(prev => ({
      ...prev,
      pendingApprovals: [...prev.pendingApprovals, approval]
    }))
  }
  
  // Remove a pending approval
  const removePendingApproval = (approvalId) => {
    setWorkflowState(prev => ({
      ...prev,
      pendingApprovals: prev.pendingApprovals.filter(a => a.id !== approvalId)
    }))
  }
  
  // Store generated output
  const storeOutput = (outputType, data) => {
    setWorkflowState(prev => ({
      ...prev,
      generatedOutputs: {
        ...prev.generatedOutputs,
        [outputType]: data
      }
    }))
  }
  
  // Toggle sidebar visibility
  const toggleSidebar = () => {
    setWorkflowState(prev => ({
      ...prev,
      showSidebar: !prev.showSidebar
    }))
  }
  
  // Prevent manual navigation to locked phases
  useEffect(() => {
    const currentPath = location.pathname
    const currentPhaseFromPath = Object.entries(workflowPhases).find(
      ([_, config]) => config.path === currentPath
    )?.[0]
    
    if (currentPhaseFromPath) {
      const phaseConfig = workflowPhases[currentPhaseFromPath]
      if (phaseConfig.requiredState && !workflowState[phaseConfig.requiredState]) {
        // Find the furthest allowed phase
        const allowedPhases = Object.entries(workflowPhases)
          .filter(([_, config]) => !config.requiredState || workflowState[config.requiredState])
          .map(([phase]) => phase)
        
        const furthestPhase = allowedPhases[allowedPhases.length - 1]
        if (furthestPhase && furthestPhase !== currentPhaseFromPath) {
          navigateToPhase(furthestPhase)
        }
      }
    }
  }, [location.pathname])
  
  // Connect to WebSocket for real-time updates
  useEffect(() => {
    let ws = null
    
    const connectWebSocket = () => {
      ws = new WebSocket(`ws://localhost:8000/ws/agent-updates`)
      
      ws.onopen = () => {
        setWorkflowState(prev => ({ ...prev, connected: true }))
      }
      
      ws.onclose = () => {
        setWorkflowState(prev => ({ ...prev, connected: false }))
        // Try to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // Handle different message types
          if (data.type === 'agent_status') {
            updateAgentProgress(data.agent, data.progress)
          } else if (data.type === 'approval_request') {
            addPendingApproval(data.approval)
          } else if (data.type === 'output_ready') {
            storeOutput(data.output_type, data.data)
          }
          
          setWorkflowState(prev => ({ ...prev, lastUpdate: new Date() }))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    }
    
    // Connect to WebSocket
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [])
  
  return (
    <WorkflowContext.Provider value={{
      workflowState,
      updateWorkflowState,
      navigateToPhase,
      nextPhase,
      transitionToAgent,
      updateAgentProgress,
      storeAgentConversation,
      addPendingApproval,
      removePendingApproval,
      storeOutput,
      toggleSidebar,
      workflowPhases
    }}>
      {children}
    </WorkflowContext.Provider>
  )
}