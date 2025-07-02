import { useState, useEffect } from 'react'
import { Brain, Users, Target, DollarSign, Megaphone, Scale, Clock, CheckCircle, AlertCircle, Loader, Star, Briefcase } from 'lucide-react'
import api from '../lib/api'
import ApprovalModal from '../components/ApprovalModal'

const AgentsPage = () => {
  const [agentsStatus, setAgentsStatus] = useState({})
  const [personalities, setPersonalities] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [selectedApproval, setSelectedApproval] = useState(null)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  
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
  
  return (
    <div className="max-w-6xl mx-auto">
      <ApprovalModal
        approval={selectedApproval}
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onSubmit={handleApprovalSubmit}
      />
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Status</h1>
        <p className="text-gray-600">
          Monitor your virtual AI team as they work on your project
        </p>
        {lastUpdate && (
          <p className="text-sm text-gray-500 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(agentsStatus).map(([agentName, status]) => {
          const Icon = agentIcons[agentName] || Brain
          const StatusIcon = statusIcons[status.status] || Clock
          const statusColor = statusColors[status.status] || statusColors.idle
          const personality = personalities[agentName] || {}
          
          return (
            <div key={agentName} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-14 h-14 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center mr-4 text-2xl">
                    {status.avatar_emoji || personality.avatar_emoji || '🤖'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {status.personality_name || personality.name || agentName}
                    </h3>
                    <p className="text-sm text-gray-600">{status.role}</p>
                    {personality.background && (
                      <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">
                        {personality.background}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                  <StatusIcon className={`h-4 w-4 mr-1 ${status.status === 'working' || status.status === 'thinking' ? 'animate-spin' : ''}`} />
                  {status.status.replace('_', ' ')}
                </div>
              </div>
              
              {/* Personality Traits */}
              {(status.traits || personality.traits) && (
                <div className="mb-3">
                  <div className="flex items-center mb-2">
                    <Brain className="h-4 w-4 text-gray-500 mr-2" />
                    <span className="text-sm font-medium text-gray-700">Traits</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {(status.traits || personality.traits || []).slice(0, 3).map((trait, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {trait.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Expertise Areas */}
              {(status.expertise_areas || personality.expertise_areas) && (
                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <Star className="h-4 w-4 text-gray-500 mr-2" />
                    <span className="text-sm font-medium text-gray-700">Expertise</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {(status.expertise_areas || personality.expertise_areas || []).slice(0, 2).map((area, index) => (
                      <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        {area.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="space-y-2 border-t pt-4">
                {status.current_task && (
                  <div>
                    <span className="text-sm font-medium text-gray-700">Current Task:</span>
                    <p className="text-sm text-gray-600">{status.current_task}</p>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">Outputs Ready:</span>
                  <span className={`font-medium ${status.outputs_ready ? 'text-green-600' : 'text-gray-500'}`}>
                    {status.outputs_ready ? 'Yes' : 'No'}
                  </span>
                </div>
                
                {status.confidence_threshold && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Confidence Threshold:</span>
                    <span className="text-gray-900 font-medium">
                      {(status.confidence_threshold * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
              
              {/* Working Style */}
              {personality.working_style && (
                <div className="mt-4 p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center mb-1">
                    <Briefcase className="h-3 w-3 text-gray-500 mr-1" />
                    <span className="text-xs font-medium text-gray-600">Working Style</span>
                  </div>
                  <p className="text-xs text-gray-600 italic">
                    "{personality.working_style}"
                  </p>
                </div>
              )}
              
              {status.status === 'completed' && status.outputs_ready && (
                <div className="mt-4 p-3 bg-green-50 rounded-md">
                  <p className="text-sm text-green-700 font-medium">
                    ✅ Task completed successfully
                  </p>
                </div>
              )}
              
              {status.status === 'error' && (
                <div className="mt-4 p-3 bg-red-50 rounded-md">
                  <p className="text-sm text-red-700 font-medium">
                    ❌ Task failed - check logs
                  </p>
                </div>
              )}
              
              {status.status === 'waiting_approval' && (
                <div className="mt-4 p-3 bg-orange-50 rounded-md">
                  <p className="text-sm text-orange-700 font-medium">
                    ⏳ Waiting for your approval
                  </p>
                  <button 
                    onClick={() => {
                      const approval = pendingApprovals.find(a => a.agent_name === agentName && a.status === 'pending');
                      if (approval) {
                        setSelectedApproval(approval);
                        setShowApprovalModal(true);
                      }
                    }}
                    className="mt-2 text-sm text-orange-600 hover:text-orange-700 font-medium">
                    Review & Approve →
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      {Object.keys(agentsStatus).length === 0 && (
        <div className="text-center py-12">
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading AI Team...</h3>
          <p className="text-gray-600">Initializing your virtual office agents with personalities</p>
        </div>
      )}
    </div>
  )
}

export default AgentsPage