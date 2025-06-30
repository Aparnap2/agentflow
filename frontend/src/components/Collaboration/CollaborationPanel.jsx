import { useState, useEffect } from 'react'
import { Users, MessageSquare, ArrowRight, Clock, CheckCircle } from 'lucide-react'
import { apiMethods } from '../../lib/api'

const CollaborationPanel = () => {
  const [collaborations, setCollaborations] = useState([])
  const [showRequestForm, setShowRequestForm] = useState(false)
  const [loading, setLoading] = useState(false)
  
  const agents = ['Marketing', 'Finance', 'Product', 'Sales', 'Legal', 'Operations']
  const requestTypes = [
    'customer_list_for_campaign',
    'budget_approval', 
    'feature_launch_campaign',
    'qualified_leads',
    'contract_review'
  ]
  
  useEffect(() => {
    fetchCollaborationHistory()
  }, [])
  
  const fetchCollaborationHistory = async () => {
    try {
      const response = await apiMethods.getCollaborationHistory()
      setCollaborations(response.collaborations || [])
    } catch (error) {
      console.error('Failed to fetch collaboration history:', error)
    }
  }
  
  const handleCollaborationRequest = async (requestingAgent, targetAgent, requestType) => {
    setLoading(true)
    try {
      const result = await apiMethods.requestCollaboration(
        requestingAgent,
        targetAgent, 
        requestType,
        {}
      )
      
      // Add to collaborations list
      setCollaborations(prev => [{
        requesting_agent: requestingAgent,
        target_agent: targetAgent,
        request_type: requestType,
        result: result,
        timestamp: new Date().toISOString()
      }, ...prev])
      
      setShowRequestForm(false)
    } catch (error) {
      console.error('Collaboration request failed:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const CollaborationRequestForm = () => {
    const [formData, setFormData] = useState({
      requestingAgent: '',
      targetAgent: '',
      requestType: ''
    })
    
    const handleSubmit = (e) => {
      e.preventDefault()
      if (formData.requestingAgent && formData.targetAgent && formData.requestType) {
        handleCollaborationRequest(
          formData.requestingAgent,
          formData.targetAgent,
          formData.requestType
        )
      }
    }
    
    return (
      <div className="bg-white rounded-lg border p-4 mb-4">
        <h3 className="font-semibold text-gray-900 mb-3">Request Agent Collaboration</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <select
              value={formData.requestingAgent}
              onChange={(e) => setFormData(prev => ({...prev, requestingAgent: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
              required
            >
              <option value="">Requesting Agent</option>
              {agents.map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
            
            <select
              value={formData.targetAgent}
              onChange={(e) => setFormData(prev => ({...prev, targetAgent: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
              required
            >
              <option value="">Target Agent</option>
              {agents.map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
          </div>
          
          <select
            value={formData.requestType}
            onChange={(e) => setFormData(prev => ({...prev, requestType: e.target.value}))}
            className="w-full px-3 py-2 border rounded-md text-sm"
            required
          >
            <option value="">Select Request Type</option>
            {requestTypes.map(type => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
          
          <div className="flex space-x-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {loading ? 'Requesting...' : 'Request Collaboration'}
            </button>
            <button
              type="button"
              onClick={() => setShowRequestForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    )
  }
  
  const formatRequestType = (type) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }
  
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Agent Collaboration</h2>
        </div>
        
        {!showRequestForm && (
          <button
            onClick={() => setShowRequestForm(true)}
            className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            New Request
          </button>
        )}
      </div>
      
      {showRequestForm && <CollaborationRequestForm />}
      
      <div className="space-y-3">
        {collaborations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>No collaborations yet. Start by requesting agent collaboration above.</p>
          </div>
        ) : (
          collaborations.map((collab, index) => (
            <div key={index} className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-blue-600">{collab.requesting_agent}</span>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  <span className="font-medium text-green-600">{collab.target_agent}</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Clock className="h-4 w-4" />
                  <span>{formatTimestamp(collab.timestamp)}</span>
                </div>
              </div>
              
              <div className="mb-3">
                <span className="text-sm font-medium text-gray-700">
                  {formatRequestType(collab.request_type)}
                </span>
              </div>
              
              {collab.result && (
                <div className="space-y-2">
                  {collab.result.success && (
                    <div className="flex items-center space-x-2 text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Collaboration Successful</span>
                    </div>
                  )}
                  
                  {collab.result.recommendations && (
                    <div className="bg-blue-50 rounded-md p-3">
                      <h4 className="text-sm font-medium text-blue-900 mb-1">Recommendations:</h4>
                      <ul className="text-sm text-blue-800 space-y-1">
                        {collab.result.recommendations.slice(0, 3).map((rec, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="w-1 h-1 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {collab.result.data && (
                    <div className="bg-gray-50 rounded-md p-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Shared Data:</h4>
                      <div className="text-sm text-gray-600">
                        {collab.result.data.high_value_customers && (
                          <div>High-value customers: {collab.result.data.high_value_customers.length}</div>
                        )}
                        {collab.result.data.qualified_leads && (
                          <div>Qualified leads: {collab.result.data.qualified_leads.length}</div>
                        )}
                        {collab.result.approved_budget && (
                          <div>Approved budget: ${collab.result.approved_budget.toLocaleString()}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default CollaborationPanel