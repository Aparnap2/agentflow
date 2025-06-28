import { useState, useEffect } from 'react'
import { Clock, User, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { apiMethods } from '../lib/api'

const TimelinePage = () => {
  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  
  useEffect(() => {
    fetchTimeline()
  }, [])
  
  const fetchTimeline = async () => {
    try {
      const data = await apiMethods.getTimeline()
      setTimeline(data)
    } catch (error) {
      console.error('Failed to fetch timeline:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const getEventIcon = (event) => {
    if (event.status === 'completed') return CheckCircle
    if (event.status === 'failed') return AlertCircle
    return FileText
  }
  
  const getEventColor = (event) => {
    if (event.status === 'completed') return 'text-green-600'
    if (event.status === 'failed') return 'text-red-600'
    return 'text-blue-600'
  }
  
  const filteredTimeline = timeline.filter(event => 
    filter === 'all' || event.agent === filter
  )
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Execution Timeline</h1>
        <p className="text-gray-600">Complete trace of agent actions and decisions</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex items-center space-x-4 mb-6">
          <select 
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Agents</option>
            <option value="Cofounder">Cofounder</option>
            <option value="Manager">Manager</option>
            <option value="Product">Product</option>
            <option value="Finance">Finance</option>
            <option value="Marketing">Marketing</option>
            <option value="Legal">Legal</option>
          </select>
        </div>
        
        <div className="space-y-6">
          {filteredTimeline.map((event, index) => {
            const Icon = getEventIcon(event)
            const colorClass = getEventColor(event)
            
            return (
              <div key={index} className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className={`p-2 rounded-full bg-gray-100 ${colorClass}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-900">{event.agent}</span>
                      <span className="text-sm text-gray-500">•</span>
                      <span className="text-sm text-gray-500">{event.timestamp}</span>
                    </div>
                    {event.confidence && (
                      <span className="text-sm text-gray-500">
                        Confidence: {(event.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-700 mt-1">{event.summary || event.action}</p>
                  
                  {event.error && (
                    <div className="mt-2 p-3 bg-red-50 rounded-md">
                      <p className="text-sm text-red-700">{event.error}</p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        
        {filteredTimeline.length === 0 && (
          <div className="text-center py-12">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Timeline Data</h3>
            <p className="text-gray-600">Start a project to see execution timeline</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TimelinePage