import { useState, useEffect } from 'react'
import { Activity, BarChart3, MessageSquare } from 'lucide-react'
import WorkflowVisualizer from '../components/WorkflowVisualizer'
import api from '../lib/api'

const WorkflowPage = () => {
  const [communicationStats, setCommunicationStats] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCommunicationStats()
    const interval = setInterval(fetchCommunicationStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchCommunicationStats = async () => {
    try {
      const stats = await api.get('/communication/stats')
      setCommunicationStats(stats.data || {})
    } catch (error) {
      console.error('Failed to fetch communication stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Workflow</h1>
        <p className="text-gray-600">Visual representation of agent collaboration and communication</p>
      </div>

      {/* Workflow Visualization */}
      <div className="mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Live Agent Network</h2>
          <WorkflowVisualizer />
        </div>
      </div>

      {/* Communication Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center mb-4">
            <MessageSquare className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Communication</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Events</span>
              <span className="font-semibold">{communicationStats.total_events || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Active Agents</span>
              <span className="font-semibold">{communicationStats.active_agents?.length || 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center mb-4">
            <BarChart3 className="h-6 w-6 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Event Types</h3>
          </div>
          <div className="space-y-2">
            {Object.entries(communicationStats.event_types || {}).map(([type, count]) => (
              <div key={type} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">{type}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center mb-4">
            <Activity className="h-6 w-6 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Agent Activity</h3>
          </div>
          <div className="space-y-2">
            {Object.entries(communicationStats.agent_activity || {}).map(([agent, count]) => (
              <div key={agent} className="flex justify-between text-sm">
                <span className="text-gray-600">{agent}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkflowPage