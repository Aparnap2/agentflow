import { useState, useEffect } from 'react'
import { useWorkflow } from '../contexts/WorkflowContext'
import AgentAvatar from '../components/AgentAvatar'
import { CheckCircle, Clock, AlertCircle, Loader, ArrowRight } from 'lucide-react'
import api from '../lib/api'

const ExecutionPage = () => {
  const [agentStatuses, setAgentStatuses] = useState({})
  const [loading, setLoading] = useState(true)
  const [allCompleted, setAllCompleted] = useState(false)
  
  const { 
    workflowState, 
    updateWorkflowState,
    nextPhase,
    transitionToAgent
  } = useWorkflow()
  
  // Fetch agent statuses
  useEffect(() => {
    const fetchAgentStatuses = async () => {
      try {
        const data = await api.getAgentsStatus()
          setAgentStatuses(data)
          
          // Check if all agents are completed
          const completedCount = Object.values(data).filter(
            agent => agent.status === 'completed'
          ).length
          
          if (completedCount >= 4) { // At least 4 specialist agents
            setAllCompleted(true)
            updateWorkflowState({ agentsCompleted: true })
          }
        }
      } catch (error) {
        console.error('Failed to fetch agent statuses:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchAgentStatuses()
    const interval = setInterval(fetchAgentStatuses, 3000)
    return () => clearInterval(interval)
  }, [])
  
  // Status colors
  const statusColors = {
    idle: 'bg-gray-100 text-gray-600',
    thinking: 'bg-yellow-100 text-yellow-700',
    working: 'bg-blue-100 text-blue-700',
    waiting_approval: 'bg-orange-100 text-orange-700',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700'
  }
  
  // Status icons
  const StatusIcon = ({ status }) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'working':
      case 'thinking':
        return <Loader className="h-5 w-5 animate-spin" />
      case 'waiting_approval':
        return <Clock className="h-5 w-5 text-orange-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }
  
  // Continue to results
  const continueToResults = () => {
    nextPhase()
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Agent Execution
        </h1>
        <p className="text-gray-600">
          Your AI team is working on your startup plan in parallel
        </p>
      </div>
      
      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading agent statuses...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {['Product', 'Finance', 'Marketing', 'Legal'].map(agentName => {
              const agent = agentStatuses[agentName] || {}
              const status = agent.status || 'idle'
              const statusColor = statusColors[status] || statusColors.idle
              
              return (
                <div 
                  key={agentName}
                  className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => transitionToAgent(agentName)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <AgentAvatar 
                        agent={agentName} 
                        size="md" 
                        pulse={status === 'working' || status === 'thinking'}
                      />
                      <div className="ml-3">
                        <h3 className="font-semibold text-gray-900">{agentName}</h3>
                        <p className="text-sm text-gray-600">{agent.role || 'Specialist'}</p>
                      </div>
                    </div>
                    
                    <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                      <StatusIcon status={status} />
                      <span className="ml-2">{status.replace('_', ' ')}</span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    {agent.current_task && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Current Task:</span>
                        <p className="text-sm text-gray-600">{agent.current_task}</p>
                      </div>
                    )}
                    
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full transition-all duration-500 ease-in-out" 
                        style={{ 
                          width: status === 'completed' ? '100%' : 
                                 status === 'working' ? '60%' : 
                                 status === 'thinking' ? '30%' : '10%' 
                        }}
                      ></div>
                    </div>
                  </div>
                  
                  {status === 'completed' && (
                    <div className="mt-4 p-3 bg-green-50 rounded-md">
                      <p className="text-sm text-green-700 font-medium">
                        ✅ Task completed successfully
                      </p>
                    </div>
                  )}
                  
                  {status === 'error' && (
                    <div className="mt-4 p-3 bg-red-50 rounded-md">
                      <p className="text-sm text-red-700 font-medium">
                        ❌ Task failed - check logs
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          
          {allCompleted && (
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                All Agents Completed!
              </h2>
              <p className="text-gray-600 mb-6">
                Your AI team has finished working on your startup plan. You can now view the results.
              </p>
              <button
                onClick={continueToResults}
                className="flex items-center px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 mx-auto"
              >
                View Results
                <ArrowRight className="h-5 w-5 ml-2" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ExecutionPage