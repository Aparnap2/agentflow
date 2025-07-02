import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle, Clock, AlertCircle, Loader, BarChart3, Settings } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts'
import api from '../lib/api'
import { useFlow } from '../contexts/FlowContext'

const TasksPage = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { updateFlowState } = useFlow()
  const { projectId, tasks } = location.state || {}
  const [taskStatuses, setTaskStatuses] = useState({})
  const [activeTab, setActiveTab] = useState('tasks')
  const [outputs, setOutputs] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (tasks) {
      const statuses = {}
      Object.keys(tasks).forEach(agent => {
        statuses[agent] = 'pending_approval'
      })
      setTaskStatuses(statuses)
    }
  }, [tasks])

  // Poll for agent status updates
  useEffect(() => {
    if (!projectId) return
    
    const pollStatus = async () => {
      try {
        const status = await api.getAgentsStatus()
        let completedCount = 0
        let totalAgents = 0
        
        Object.keys(tasks || {}).forEach(agent => {
          totalAgents++
          if (status[agent]?.status === 'completed') {
            setTaskStatuses(prev => ({ ...prev, [agent]: 'completed' }))
            completedCount++
          } else if (status[agent]?.status === 'working' || status[agent]?.status === 'thinking') {
            setTaskStatuses(prev => ({ ...prev, [agent]: 'running' }))
          }
        })
        
        // If all agents are completed, update flow state
        if (completedCount > 0 && completedCount === totalAgents) {
          console.log('All agents completed!')
          updateFlowState({ 
            tasksDistributed: true,
            agentsCompleted: true 
          })
          
          // Navigate to outputs page after a short delay
          setTimeout(() => {
            navigate('/outputs')
          }, 2000)
        }
        
        setLoading(false)
      } catch (error) {
        console.error('Failed to poll status:', error)
        setLoading(false)
      }
    }
    
    // Set a timeout to stop loading after 10 seconds even if no response
    const loadingTimeout = setTimeout(() => {
      setLoading(false)
      // Force update flow state to allow navigation
      updateFlowState({ 
        tasksDistributed: true
      })
    }, 10000)
    
    const interval = setInterval(pollStatus, 3000)
    pollStatus() // Initial call
    
    return () => {
      clearInterval(interval)
      clearTimeout(loadingTimeout)
    }
  }, [projectId, tasks, navigate, updateFlowState])

  // Fetch outputs for visualization
  useEffect(() => {
    const fetchOutputs = async () => {
      try {
        const data = await api.getOutputs()
        setOutputs(data)
        
        // If we have outputs, update flow state
        if (Object.keys(data).length > 0) {
          updateFlowState({ tasksDistributed: true })
        }
      } catch (error) {
        console.error('Failed to fetch outputs:', error)
      }
    }
    fetchOutputs()
    
    // Poll for outputs every 5 seconds
    const interval = setInterval(fetchOutputs, 5000)
    return () => clearInterval(interval)
  }, [updateFlowState])

  const handleTaskAction = async (agent, action) => {
    try {
      setTaskStatuses(prev => ({ ...prev, [agent]: 'processing' }))
      
      if (action === 'approve') {
        await api.executeAgent(agent, tasks[agent])
        setTaskStatuses(prev => ({ ...prev, [agent]: 'running' }))
        
        // Update flow state to indicate tasks are distributed
        updateFlowState({
          tasksDistributed: true
        })
      } else {
        setTaskStatuses(prev => ({ ...prev, [agent]: 'denied' }))
      }
    } catch (error) {
      console.error(`Failed to ${action} task:`, error)
      setTaskStatuses(prev => ({ ...prev, [agent]: 'error' }))
    }
  }

  const getStatusBadge = (status) => {
    const configs = {
      pending_approval: { icon: Clock, color: 'bg-orange-100 text-orange-700', text: 'Pending Approval' },
      processing: { icon: Loader, color: 'bg-blue-100 text-blue-700', text: 'Processing' },
      running: { icon: Loader, color: 'bg-blue-100 text-blue-700', text: 'Running' },
      approved: { icon: CheckCircle, color: 'bg-green-100 text-green-700', text: 'Approved' },
      completed: { icon: CheckCircle, color: 'bg-green-100 text-green-700', text: 'Completed' },
      denied: { icon: AlertCircle, color: 'bg-red-100 text-red-700', text: 'Denied' },
      error: { icon: AlertCircle, color: 'bg-red-100 text-red-700', text: 'Error' }
    }
    const config = configs[status] || configs.pending_approval
    const Icon = config.icon
    return (
      <div className={`flex items-center px-3 py-1 rounded-full text-sm ${config.color}`}>
        <Icon className={`h-4 w-4 mr-1 ${status === 'processing' || status === 'running' ? 'animate-spin' : ''}`} />
        {config.text}
      </div>
    )
  }

  const getVisualizationData = () => {
    const statusData = Object.entries(taskStatuses).map(([agent, status]) => ({
      agent, status, count: 1
    }))
    
    const financeData = outputs['finance.json']?.data
    
    return { statusData, financeData }
  }

  const { statusData, financeData } = getVisualizationData()
  const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#3B82F6']

  if (!tasks) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">No tasks found</h2>
        <p className="text-gray-600">Please start a conversation first</p>
      </div>
    )
  }
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
        <p className="text-gray-600">Loading agent statuses...</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Project Dashboard</h1>
        <p className="text-gray-600">Monitor agents, visualize data, and customize workflows</p>
        <p className="text-sm text-gray-500">Project ID: {projectId}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'tasks', label: 'Agent Tasks', icon: CheckCircle },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'customize', label: 'Customize', icon: Settings }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4 mr-2" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tasks Tab */}
      {activeTab === 'tasks' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(tasks).map(([agent, task]) => (
            <div key={agent} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{agent} Agent</h3>
                {getStatusBadge(taskStatuses[agent] || 'pending_approval')}
              </div>
              
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium text-gray-700">Task Type:</span>
                  <p className="text-sm text-gray-600">{task.type}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-700">Description:</span>
                  <p className="text-sm text-gray-600">{task.description}</p>
                </div>
                
                <div className="pt-4 border-t">
                  <div className="flex space-x-3">
                    <button 
                      onClick={() => handleTaskAction(agent, 'approve')}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                    >
                      ✅ Approve
                    </button>
                    <button 
                      onClick={() => handleTaskAction(agent, 'deny')}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
                    >
                      ❌ Deny
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Agent Status Chart */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold mb-4">Agent Status</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    label={({ agent }) => agent}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Financial Projections */}
            {financeData?.financial_projections && (
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold mb-4">Revenue Projections</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={Object.entries(financeData.financial_projections).map(([year, data]) => ({
                    year: year.replace('year_', 'Year '),
                    revenue: data.revenue,
                    costs: data.costs
                  }))}>
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Bar dataKey="revenue" fill="#10B981" name="Revenue" />
                    <Bar dataKey="costs" fill="#EF4444" name="Costs" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {financeData && [
              { label: 'Break Even', value: financeData.roi_analysis?.break_even_point || 'TBD', color: 'blue' },
              { label: 'LTV/CAC Ratio', value: financeData.roi_analysis?.ltv_cac_ratio || 'TBD', color: 'green' },
              { label: 'Payback Period', value: financeData.roi_analysis?.payback_period || 'TBD', color: 'purple' },
              { label: 'Funding Need', value: `$${(financeData.funding_requirements?.seed_funding || 0).toLocaleString()}`, color: 'orange' }
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-white p-4 rounded-lg shadow-sm border">
                <div className={`text-2xl font-bold text-${color}-600`}>{value}</div>
                <div className="text-sm text-gray-600">{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Customize Tab */}
      {activeTab === 'customize' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Agent Configuration</h3>
          <div className="space-y-4">
            {Object.keys(tasks).map(agent => (
              <div key={agent} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">{agent} Agent</h4>
                  {getStatusBadge(taskStatuses[agent] || 'pending_approval')}
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="block text-gray-700 mb-1">Approval Mode</label>
                    <select className="w-full border rounded px-2 py-1">
                      <option>Manual</option>
                      <option>Auto</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-gray-700 mb-1">Priority</label>
                    <select className="w-full border rounded px-2 py-1">
                      <option>High</option>
                      <option>Medium</option>
                      <option>Low</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default TasksPage