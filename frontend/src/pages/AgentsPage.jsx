import { useState, useEffect } from 'react'
import { Brain, Users, Target, DollarSign, Megaphone, Scale, Clock, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import api from '../lib/api'

const AgentsPage = () => {
  const [agentsStatus, setAgentsStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  
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
    const interval = setInterval(fetchAgentsStatus, 3000) // Poll every 3 seconds
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
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="max-w-6xl mx-auto">
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
          
          return (
            <div key={agentName} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="p-2 bg-primary-100 rounded-lg mr-3">
                    <Icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{agentName}</h3>
                    <p className="text-sm text-gray-600">{status.role}</p>
                  </div>
                </div>
                
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                  <StatusIcon className={`h-4 w-4 mr-1 ${status.status === 'working' || status.status === 'thinking' ? 'animate-spin' : ''}`} />
                  {status.status.replace('_', ' ')}
                </div>
              </div>
              
              <div className="space-y-2">
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
              </div>
              
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
                  <button className="mt-2 text-sm text-orange-600 hover:text-orange-700 font-medium">
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
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Agents</h3>
          <p className="text-gray-600">Start a project to see your AI team in action</p>
        </div>
      )}
    </div>
  )
}

export default AgentsPage