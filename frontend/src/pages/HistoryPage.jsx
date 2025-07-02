import { useState, useEffect } from 'react'
import { Clock, CheckCircle, AlertCircle, Brain, Users, Target, DollarSign, Megaphone, Scale } from 'lucide-react'
import api from '../lib/api'

const HistoryPage = () => {
  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const agentIcons = {
    Cofounder: Brain,
    Manager: Users,
    Product: Target,
    Finance: DollarSign,
    Marketing: Megaphone,
    Legal: Scale
  }

  useEffect(() => {
    fetchTimeline()
    const interval = setInterval(fetchTimeline, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchTimeline = async () => {
    try {
      const data = await api.get('/timeline')
      setTimeline(data.data || [])
    } catch (error) {
      console.error('Failed to fetch timeline:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredTimeline = timeline.filter(entry => {
    if (filter === 'all') return true
    if (filter === 'completed') return entry.status === 'completed'
    if (filter === 'failed') return entry.status === 'failed'
    return entry.agent === filter
  })

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed': return <AlertCircle className="h-5 w-5 text-red-500" />
      default: return <Clock className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-50 border-green-200'
      case 'failed': return 'bg-red-50 border-red-200'
      default: return 'bg-yellow-50 border-yellow-200'
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
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Project History</h1>
        <p className="text-gray-600">Timeline of all agent activities and project milestones</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-2">
        {['all', 'completed', 'failed', 'Cofounder', 'Manager', 'Product', 'Finance', 'Marketing', 'Legal'].map(filterOption => (
          <button
            key={filterOption}
            onClick={() => setFilter(filterOption)}
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              filter === filterOption
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {filteredTimeline.length > 0 ? (
          filteredTimeline.map((entry, index) => {
            const AgentIcon = agentIcons[entry.agent] || Brain
            return (
              <div key={index} className={`border rounded-lg p-4 ${getStatusColor(entry.status)}`}>
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center border-2 border-gray-200">
                      <AgentIcon className="h-5 w-5 text-gray-600" />
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-gray-900">{entry.agent} Agent</h3>
                        {getStatusIcon(entry.status)}
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                    </div>
                    
                    {entry.summary && (
                      <p className="text-gray-700 mb-2">{entry.summary}</p>
                    )}
                    
                    {entry.confidence && (
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm text-gray-600">Confidence:</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full" 
                            style={{ width: `${entry.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">{Math.round(entry.confidence * 100)}%</span>
                      </div>
                    )}
                    
                    {entry.error && (
                      <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-700">
                        <strong>Error:</strong> {entry.error}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="text-center py-12">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No History Available</h3>
            <p className="text-gray-600">Start a project to see the timeline of agent activities</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default HistoryPage