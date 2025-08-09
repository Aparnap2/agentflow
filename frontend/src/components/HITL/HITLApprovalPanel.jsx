import { useState, useEffect } from 'react'
import { Clock, CheckCircle, XCircle, AlertTriangle, User, MessageSquare } from 'lucide-react'
import prdApi from '../../lib/prd-api'

const HITLApprovalPanel = () => {
  const [approvals, setApprovals] = useState([])
  const [loading, setLoading] = useState(false)
  const [processingId, setProcessingId] = useState(null)

  useEffect(() => {
    fetchPendingApprovals()
    // Poll for new approvals every 30 seconds
    const interval = setInterval(fetchPendingApprovals, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchPendingApprovals = async () => {
    try {
      const data = await prdApi.getPendingApprovals()
      setApprovals(data.approvals || [])
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error)
    }
  }

  const handleApproval = async (approvalId, action, feedback = '') => {
    setProcessingId(approvalId)
    setLoading(true)
    
    try {
      await prdApi.handleApproval(approvalId, action, feedback)
      
      // Remove approved item from list
      setApprovals(prev => prev.filter(approval => approval.id !== approvalId))
      
      // Show success message
      console.log(`Approval ${action}ed successfully`)
    } catch (error) {
      console.error('Failed to process approval:', error)
    } finally {
      setLoading(false)
      setProcessingId(null)
    }
  }

  const ApprovalCard = ({ approval }) => {
    const [showFeedback, setShowFeedback] = useState(false)
    const [feedback, setFeedback] = useState('')

    const getPriorityColor = (type) => {
      switch (type) {
        case 'instagram_post':
        case 'dm_response':
          return 'border-l-orange-500 bg-orange-50'
        case 'crm_stage_move':
        case 'financial_decision':
          return 'border-l-red-500 bg-red-50'
        case 'strategic_decision':
          return 'border-l-purple-500 bg-purple-50'
        default:
          return 'border-l-blue-500 bg-blue-50'
      }
    }

    const getTypeIcon = (type) => {
      switch (type) {
        case 'instagram_post':
        case 'dm_response':
          return <MessageSquare className="h-5 w-5 text-orange-600" />
        case 'crm_stage_move':
          return <User className="h-5 w-5 text-red-600" />
        case 'financial_decision':
          return <AlertTriangle className="h-5 w-5 text-red-600" />
        default:
          return <Clock className="h-5 w-5 text-blue-600" />
      }
    }

    const formatType = (type) => {
      return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    return (
      <div className={`border-l-4 rounded-lg p-4 mb-4 ${getPriorityColor(approval.type)}`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            {getTypeIcon(approval.type)}
            <div>
              <h3 className="font-semibold text-gray-900">
                {formatType(approval.type)}
              </h3>
              <p className="text-sm text-gray-600">
                Requested by: <span className="font-medium">{approval.requested_by}</span>
              </p>
            </div>
          </div>
          <div className="text-right text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{new Date(approval.created_at).toLocaleString()}</span>
            </div>
            {approval.expires_at && (
              <div className="text-xs text-red-600 mt-1">
                Expires: {new Date(approval.expires_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        {approval.reasoning && (
          <div className="mb-3 p-3 bg-white rounded border">
            <h4 className="text-sm font-medium text-gray-700 mb-1">Reasoning:</h4>
            <p className="text-sm text-gray-600">{approval.reasoning}</p>
          </div>
        )}

        {approval.payload && (
          <div className="mb-4 p-3 bg-white rounded border">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Details:</h4>
            <div className="text-sm text-gray-600 space-y-1">
              {approval.payload.agent_output && (
                <div>
                  <span className="font-medium">Confidence:</span> {
                    (approval.payload.confidence * 100).toFixed(1)
                  }%
                </div>
              )}
              {approval.payload.action_description && (
                <div>
                  <span className="font-medium">Action:</span> {approval.payload.action_description}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleApproval(approval.id, 'approve')}
            disabled={loading && processingId === approval.id}
            className="flex items-center space-x-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
          >
            <CheckCircle className="h-4 w-4" />
            <span>{loading && processingId === approval.id ? 'Approving...' : 'Approve'}</span>
          </button>
          
          <button
            onClick={() => handleApproval(approval.id, 'reject')}
            disabled={loading && processingId === approval.id}
            className="flex items-center space-x-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 text-sm"
          >
            <XCircle className="h-4 w-4" />
            <span>Reject</span>
          </button>
          
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
          >
            Request Changes
          </button>
        </div>

        {showFeedback && (
          <div className="mt-3 p-3 bg-white rounded border">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Provide feedback for changes..."
              className="w-full p-2 border rounded-md text-sm"
              rows={3}
            />
            <div className="flex space-x-2 mt-2">
              <button
                onClick={() => handleApproval(approval.id, 'request_changes', feedback)}
                disabled={!feedback.trim() || (loading && processingId === approval.id)}
                className="px-3 py-1 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 text-sm"
              >
                Send Feedback
              </button>
              <button
                onClick={() => setShowFeedback(false)}
                className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          <h2 className="text-lg font-semibold text-gray-900">HITL Approvals</h2>
          {approvals.length > 0 && (
            <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {approvals.length} pending
            </span>
          )}
        </div>
        
        <button
          onClick={fetchPendingApprovals}
          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        {approvals.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>No pending approvals. All workflows are running smoothly!</p>
          </div>
        ) : (
          approvals.map((approval) => (
            <ApprovalCard key={approval.id} approval={approval} />
          ))
        )}
      </div>
    </div>
  )
}

export default HITLApprovalPanel