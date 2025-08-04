import { useState, useEffect } from 'react'
import { Brain, Users, Target, DollarSign, Megaphone, Scale, Play, Pause, Square, Settings, Activity } from 'lucide-react'
import api from '../lib/api'
import ApprovalModal from '../components/ApprovalModal'
import { StatusIndicator, LoadingSpinner } from '../components/shared'

const AgentsPage = () => {
  const [agentsStatus, setAgentsStatus] = useState({})
  const [personalities, setPersonalities] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [selectedApproval, setSelectedApproval] = useState(null)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showConfig, setShowConfig] = useState(false)
  
  const agentIcons = {
    Cofounder: Brain,
    Manager: Users,
    Product: Target,
    Finance: DollarSign,
    Marketing: Megaphone,
    Legal: Scale
  }
  
  const statusColors = {
    idle: 'bg-gray-100 text-gray-600',
    thinking: 'bg-yellow-100 text-yellow-700',
    working: 'bg-blue-100 text-blue-700',
    waiting_approval: 'bg-orange-100 text-orange-700',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700'
  }
  
  const statusIcons = {
    idle: Clock,
    thinking: Loader,
    working: Loader,
    waiting_approval: AlertCircle,
    completed: CheckCircle,
    error: AlertCircle
  }
  
  useEffect(() => {
    fetchAgentsStatus()
    fetchPersonalities()
    fetchPendingApprovals()
    const interval = setInterval(() => {
      fetchAgentsStatus()
      fetchPendingApprovals()
    }, 3000) // Poll every 3 seconds
    return () => clearInterval(interval)
  }, [])
  
  const fetchAgentsStatus = async () => {
    try {
      const status = await api.getAgentsStatus()
      setAgentsStatus(status)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch agents status:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchPersonalities = async () => {
    try {
      const response = await fetch('/api/agents/personalities')
      if (response.ok) {
        const data = await response.json()
        setPersonalities(data)
      }
    } catch (error) {
      console.error('Failed to fetch personalities:', error)
    }
  }

  const fetchPendingApprovals = async () => {
    try {
      // The API returns an object like { approvals: [...] }
      const response = await api.getPendingApprovals();
      setPendingApprovals(response.approvals || []);
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error);
    }
  };

  const handleApprovalSubmit = async (id, action, feedback) => {
    await api.respondToApproval(id, action, feedback);
    setShowApprovalModal(false);
    setSelectedApproval(null);
    fetchAgentsStatus();
    fetchPendingApprovals();
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  const handleAgentAction = async (agentName, action) => {
    try {
      if (action === 'start') {
        await api.executeAgent(agentName, { type: 'general_task' })
      } else if (action === 'pause') {
        // Implement pause logic
        console.log(`Pausing ${agentName}`)
      } else if (action === 'stop') {
        // Implement stop logic
        console.log(`Stopping ${agentName}`)
      }
      fetchAgentsStatus() // Refresh status
    } catch (error) {
      console.error(`Failed to ${action} agent:`, error)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <ApprovalModal
        approval={selectedApproval}
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onSubmit={handleApprovalSubmit}
      />
      
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">AI Agent Team</h1>
            <p className="text-gray-600">
              Monitor and control your virtual AI team
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-4">
            {lastUpdate && (
              <p className="text-sm text-gray-500">
                Updated: {lastUpdate.toLocaleTimeString()}
              </p>
            )}
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="flex items-center px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <Settings className="h-4 w-4 mr-2" />
              Config
            </button>
          </div>
        </div>
      </div>
      
      {/* Agent Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {Object.entries(agentsStatus).map(([agentName, status]) => {
          const Icon = agentIcons[agentName] || Brain
          const StatusIcon = statusIcons[status.status] || Clock
          const statusColor = statusColors[status.status] || statusColors.idle
          const personality = personalities[agentName] || {}
          
          return (
            <div key={agentName} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-all duration-200">
              {/* Agent Header */}
              <div className="p-4 sm:p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center min-w-0 flex-1">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center mr-3 text-xl sm:text-2xl flex-shrink-0">
                      {status.avatar_emoji || personality.avatar_emoji || '🤖'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-gray-900 truncate">
                        {status.personality_name || personality.name || agentName}
                      </h3>
                      <p className="text-sm text-gray-600 truncate">{status.role}</p>
                    </div>
                  </div>
                  
                  <StatusIndicator 
                    status={status.status} 
                    size="sm" 
                    showText={false}
                  />
                </div>
                
                {/* Current Task */}
                {status.current_task && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800 font-medium mb-1">Current Task</p>
                    <p className="text-sm text-blue-700">{status.current_task}</p>
                  </div>
                )}
                
                {/* Quick Stats */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-lg font-bold text-gray-900">
                      {status.outputs_ready ? '✅' : '⏳'}
                    </div>
                    <div className="text-xs text-gray-600">Output</div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-lg font-bold text-gray-900">
                      {status.confidence ? Math.round(status.confidence * 100) + '%' : 'N/A'}
                    </div>
                    <div className="text-xs text-gray-600">Confidence</div>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex space-x-2">
                  {status.status === 'idle' && (
                    <button 
                      onClick={() => handleAgentAction(agentName, 'start')}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Start
                    </button>
                  )}
                  {status.status === 'working' && (
                    <button 
                      onClick={() => handleAgentAction(agentName, 'pause')}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 text-sm font-medium"
                    >
                      <Pause className="h-4 w-4 mr-1" />
                      Pause
                    </button>
                  )}
                  {status.status !== 'idle' && (
                    <button 
                      onClick={() => handleAgentAction(agentName, 'stop')}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium"
                    >
                      <Square className="h-4 w-4 mr-1" />
                      Stop
                    </button>
                  )}
                  <button 
                    onClick={() => {
                      setSelectedAgent(agentName)
                      setShowConfig(true)
                    }}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
                  >
                    <Settings className="h-4 w-4" />
                  </button>
                </div>
                
                {/* Status Messages */}
                {status.status === 'waiting_approval' && (
                  <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-md">
                    <p className="text-sm text-orange-800 font-medium mb-2">⏳ Waiting for approval</p>
                    <button 
                      onClick={() => {
                        const approval = pendingApprovals.find(a => a.agent_name === agentName && a.status === 'pending');
                        if (approval) {
                          setSelectedApproval(approval);
                          setShowApprovalModal(true);
                        }
                      }}
                      className="text-sm text-orange-600 hover:text-orange-700 font-medium">
                      Review & Approve →
                    </button>
                  </div>
                )}
                
                {status.status === 'completed' && (
                  <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-800 font-medium">✅ Task completed successfully</p>
                  </div>
                )}
                
                {status.status === 'error' && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800 font-medium">❌ Task failed - check logs</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Empty State */}
      {Object.keys(agentsStatus).length === 0 && (
        <LoadingSpinner size="lg" text="Initializing your virtual office agents" />
      )}
    </div>
  )
}

export default AgentsPage