import { useState, useEffect } from 'react'
import { useWorkflow } from '../contexts/WorkflowContext'
import AgentAvatar from './AgentAvatar'
import { 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader,
  MessageSquare,
  FileText,
  BarChart
} from 'lucide-react'

const WorkflowSidebar = () => {
  const { 
    workflowState, 
    workflowPhases, 
    toggleSidebar,
    navigateToPhase,
    transitionToAgent
  } = useWorkflow()
  
  const [agentPersonalities, setAgentPersonalities] = useState({})
  
  // Fetch agent personalities
  useEffect(() => {
    const fetchPersonalities = async () => {
      try {
        const response = await fetch('/api/agents/personalities')
        if (response.ok) {
          const data = await response.json()
          setAgentPersonalities(data)
        }
      } catch (error) {
        console.error('Failed to fetch personalities:', error)
      }
    }
    
    fetchPersonalities()
  }, [])
  
  // Phase status indicators
  const getPhaseStatus = (phase) => {
    const currentPhase = workflowState.currentPhase
    const phaseConfig = workflowPhases[phase]
    
    if (currentPhase === phase) {
      return 'active'
    }
    
    // Check if phase is completed
    if (phaseConfig.requiredState && workflowState[phaseConfig.requiredState]) {
      return 'completed'
    }
    
    // Check if phase is accessible
    if (!phaseConfig.requiredState || workflowState[phaseConfig.requiredState]) {
      return 'accessible'
    }
    
    return 'locked'
  }
  
  // Phase status icons
  const PhaseStatusIcon = ({ status }) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'active':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />
      case 'accessible':
        return <Clock className="h-5 w-5 text-gray-400" />
      case 'locked':
        return <AlertCircle className="h-5 w-5 text-gray-300" />
      default:
        return null
    }
  }
  
  // Phase icons
  const phaseIcons = {
    introduction: MessageSquare,
    vision: Brain,
    planning: FileText,
    execution: Users,
    results: BarChart,
    dashboard: BarChart
  }
  
  // Get agent progress percentage
  const getAgentProgress = (agentName) => {
    return workflowState.agentProgress[agentName] || 0
  }
  
  // Get agent personality name
  const getAgentPersonalityName = (agentName) => {
    return agentPersonalities[agentName]?.name || agentName
  }
  
  return (
    <div className={`
      ${workflowState.showSidebar ? 'w-64' : 'w-16'} 
      h-screen fixed left-0 top-0 bg-white border-r shadow-sm
      transition-all duration-300 ease-in-out z-10
    `}>
      <div className="flex flex-col h-full">
        {/* Sidebar header */}
        <div className="p-4 border-b flex items-center justify-between">
          {workflowState.showSidebar && (
            <h2 className="font-semibold text-gray-900">AgentFlow</h2>
          )}
          <button 
            onClick={toggleSidebar}
            className="p-1 rounded-md hover:bg-gray-100"
          >
            {workflowState.showSidebar ? (
              <ChevronLeft className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-500" />
            )}
          </button>
        </div>
        
        {/* Workflow phases */}
        <div className="p-4 border-b">
          {workflowState.showSidebar && (
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-4">
              Workflow
            </h3>
          )}
          
          <div className="space-y-2">
            {Object.entries(workflowPhases).map(([phase, config]) => {
              const status = getPhaseStatus(phase)
              const PhaseIcon = phaseIcons[phase] || MessageSquare
              
              return (
                <button
                  key={phase}
                  onClick={() => status !== 'locked' && navigateToPhase(phase)}
                  disabled={status === 'locked'}
                  className={`
                    w-full flex items-center p-2 rounded-md
                    ${status === 'active' ? 'bg-primary-50 text-primary-700' : ''}
                    ${status === 'locked' ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'}
                  `}
                >
                  <PhaseIcon className={`
                    h-5 w-5 
                    ${status === 'active' ? 'text-primary-600' : 'text-gray-500'}
                    ${!workflowState.showSidebar ? 'mx-auto' : ''}
                  `} />
                  
                  {workflowState.showSidebar && (
                    <>
                      <span className="ml-3 flex-1 text-left">
                        {phase.charAt(0).toUpperCase() + phase.slice(1)}
                      </span>
                      <PhaseStatusIcon status={status} />
                    </>
                  )}
                </button>
              )
            })}
          </div>
        </div>
        
        {/* Agent team */}
        <div className="p-4 flex-1 overflow-y-auto">
          {workflowState.showSidebar && (
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-4">
              Agent Team
            </h3>
          )}
          
          <div className="space-y-3">
            {['Cofounder', 'Manager', 'Product', 'Finance', 'Marketing', 'Legal', 'Sales', 'Operations'].map(agentName => {
              const isActive = workflowState.activeAgent === agentName
              const progress = getAgentProgress(agentName)
              const personalityName = getAgentPersonalityName(agentName)
              
              return (
                <button
                  key={agentName}
                  onClick={() => transitionToAgent(agentName)}
                  className={`
                    w-full flex items-center p-2 rounded-md
                    ${isActive ? 'bg-primary-50' : 'hover:bg-gray-100'}
                  `}
                >
                  <div className={!workflowState.showSidebar ? 'mx-auto' : ''}>
                    <AgentAvatar 
                      agent={agentName} 
                      size="sm" 
                      showStatus={isActive}
                      speaking={isActive && workflowState.agentSpeaking}
                    />
                  </div>
                  
                  {workflowState.showSidebar && (
                    <div className="ml-3 flex-1">
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${isActive ? 'text-primary-700' : 'text-gray-700'}`}>
                          {personalityName}
                        </span>
                        <span className="text-xs text-gray-500">
                          {progress}%
                        </span>
                      </div>
                      
                      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <div 
                          className="bg-primary-600 h-1.5 rounded-full" 
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </div>
        
        {/* Sidebar footer */}
        {workflowState.showSidebar && (
          <div className="p-4 border-t">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full ${workflowState.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="ml-2 text-xs text-gray-500">
                  {workflowState.connected ? 'Connected' : 'Reconnecting...'}
                </span>
              </div>
              
              {workflowState.lastUpdate && (
                <span className="text-xs text-gray-500">
                  Updated {new Date(workflowState.lastUpdate).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default WorkflowSidebar