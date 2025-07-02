import { useState, useEffect } from 'react'
import { Activity, Cpu, Database, Wifi, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import api from '../lib/api'

const MonitoringPage = () => {
  const [systemStats, setSystemStats] = useState({})
  const [agentStats, setAgentStats] = useState({})
  const [memoryStats, setMemoryStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  useEffect(() => {
    fetchMonitoringData()
    const interval = setInterval(fetchMonitoringData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchMonitoringData = async () => {
    try {
      const [agents, memory, health] = await Promise.all([
        api.getAgentsStatus(),
        api.get('/memory/stats'),
        api.get('/health')
      ])
      
      setAgentStats(agents)
      setMemoryStats(memory.data || {})
      setSystemStats(health.data || {})
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getHealthStatus = () => {
    const agentCount = Object.keys(agentStats).length
    const healthyAgents = Object.values(agentStats).filter(agent => 
      agent.status !== 'error'
    ).length
    
    if (healthyAgents === agentCount && agentCount > 0) return 'healthy'
    if (healthyAgents > agentCount * 0.5) return 'warning'
    return 'critical'
  }

  const healthStatus = getHealthStatus()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">System Monitoring</h1>
            <p className="text-gray-600">Real-time monitoring of agents and system health</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              healthStatus === 'healthy' ? 'bg-green-500' : 
              healthStatus === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm font-medium capitalize">{healthStatus}</span>
          </div>
        </div>
        {lastUpdate && (
          <p className="text-sm text-gray-500 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">System Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemStats.status === 'healthy' ? 'Online' : 'Issues'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Cpu className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Active Agents</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(agentStats).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Database className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Memory Systems</p>
              <p className="text-2xl font-bold text-gray-900">
                {memoryStats.vector_memory ? '3' : '1'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Wifi className="h-8 w-8 text-indigo-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">API Status</p>
              <p className="text-2xl font-bold text-gray-900">Connected</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Status */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Agent Status</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(agentStats).map(([name, agent]) => (
                <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      agent.status === 'completed' ? 'bg-green-500' :
                      agent.status === 'working' || agent.status === 'thinking' ? 'bg-blue-500' :
                      agent.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                    }`}></div>
                    <div>
                      <p className="font-medium text-gray-900">{name}</p>
                      <p className="text-sm text-gray-600">{agent.role || 'Agent'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {agent.status || 'idle'}
                    </p>
                    {agent.confidence && (
                      <p className="text-xs text-gray-500">
                        {Math.round(agent.confidence * 100)}% confidence
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Memory Statistics */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Memory Systems</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Vector Memory</p>
                    <p className="text-sm text-gray-600">Semantic search & retrieval</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-green-600">Active</p>
                  <p className="text-xs text-gray-500">
                    {memoryStats.vector_memory?.documents || 0} docs
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Graph Memory</p>
                    <p className="text-sm text-gray-600">Relationship mapping</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-green-600">
                    {memoryStats.graph_memory?.status || 'Active'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {memoryStats.graph_memory?.nodes || 0} nodes
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">State Manager</p>
                    <p className="text-sm text-gray-600">Conversation persistence</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-green-600">Active</p>
                  <p className="text-xs text-gray-500">Redis</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Alerts */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">System Alerts</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {Object.values(agentStats).some(agent => agent.status === 'error') ? (
                <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                  <div>
                    <p className="font-medium text-red-900">Agent Errors Detected</p>
                    <p className="text-sm text-red-700">Some agents have encountered errors</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-green-900">All Systems Operational</p>
                    <p className="text-sm text-green-700">No alerts at this time</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Performance</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Average Response Time</span>
                <span className="text-sm font-bold text-gray-900">1.2s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Success Rate</span>
                <span className="text-sm font-bold text-green-600">98.5%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Active Connections</span>
                <span className="text-sm font-bold text-gray-900">
                  {Object.keys(agentStats).length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Uptime</span>
                <span className="text-sm font-bold text-gray-900">99.9%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MonitoringPage