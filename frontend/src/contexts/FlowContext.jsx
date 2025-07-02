import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const FlowContext = createContext()

export const useFlow = () => {
  const context = useContext(FlowContext)
  if (!context) {
    throw new Error('useFlow must be used within FlowProvider')
  }
  return context
}

export const FlowProvider = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  
  const [flowState, setFlowState] = useState({
    currentStep: 'conversation',
    conversationId: null,
    projectId: null,
    visionApproved: false,
    tasksDistributed: false,
    agentsCompleted: false,
    canNavigate: {
      start: true,
      conversation: true,
      tasks: false,
      outputs: false,
      reports: false
    }
  })

  const flowSteps = {
    start: { path: '/', next: 'conversation' },
    conversation: { path: '/conversation', next: 'tasks' },
    tasks: { path: '/tasks', next: 'outputs' },
    outputs: { path: '/outputs', next: 'reports' },
    reports: { path: '/reports', next: null }
  }

  const updateFlowState = (updates) => {
    setFlowState(prev => {
      const newState = { ...prev, ...updates }
      
      // Update navigation permissions based on progress
      const canNavigate = {
        start: true,
        conversation: newState.conversationId !== null,
        tasks: newState.visionApproved,
        outputs: newState.tasksDistributed,
        reports: newState.agentsCompleted
      }
      
      return { ...newState, canNavigate }
    })
  }

  const navigateToStep = (step) => {
    if (flowState.canNavigate[step]) {
      const stepConfig = flowSteps[step]
      if (stepConfig) {
        setFlowState(prev => ({ ...prev, currentStep: step }))
        navigate(stepConfig.path)
      }
    }
  }

  const nextStep = () => {
    const currentStepConfig = flowSteps[flowState.currentStep]
    if (currentStepConfig?.next && flowState.canNavigate[currentStepConfig.next]) {
      navigateToStep(currentStepConfig.next)
    }
  }

  // Prevent manual navigation to locked steps
  useEffect(() => {
    const currentPath = location.pathname
    const currentStepFromPath = Object.entries(flowSteps).find(
      ([_, config]) => config.path === currentPath
    )?.[0]
    
    if (currentStepFromPath && !flowState.canNavigate[currentStepFromPath]) {
      // Redirect to the furthest allowed step
      const allowedSteps = Object.entries(flowState.canNavigate)
        .filter(([_, allowed]) => allowed)
        .map(([step]) => step)
      
      const furthestStep = allowedSteps[allowedSteps.length - 1]
      if (furthestStep && furthestStep !== currentStepFromPath) {
        navigateToStep(furthestStep)
      }
    }
  }, [location.pathname, flowState.canNavigate])

  return (
    <FlowContext.Provider value={{
      flowState,
      updateFlowState,
      navigateToStep,
      nextStep,
      flowSteps
    }}>
      {children}
    </FlowContext.Provider>
  )
}