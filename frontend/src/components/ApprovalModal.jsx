import { useState } from 'react'
import { X, Check, AlertTriangle, Edit, RotateCcw, Clock, User, FileText } from 'lucide-react'

const ApprovalModal = ({ approval, onResponse, onClose }) => {
  const [feedback, setFeedback] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  
  const handleResponse = async (action) => {
    setIsProcessing(true)
    try {
      await onResponse(approval.id, action, feedback)
      setFeedback('')
    } catch (error) {
      console.error('Failed to process approval:', error)
    } finally {
      setIsProcessing(false)
    }
  }
  
  if (!approval) return null

  const formatContent = (content) => {
    if (typeof content === 'string') return content
    if (typeof content === 'object') {
      return JSON.stringify(content, null, 2)
    }
    return String(content)
  }
  
  const getActionTypeDisplay = (actionType) => {
    const types = {
      'task_completion': 'Task Completion',
      'memory_write': 'Memory Write',
      'api_call': 'API Call',
      'tool_usage': 'Tool Usage'
    }
    return types[actionType] || actionType
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-orange-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-full">
              <AlertTriangle className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Approval Required
              </h2>
              <p className="text-sm text-gray-600">
                Agent {approval.agent_name} is requesting approval
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Approval Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <User className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">Agent</p>
                <p className="text-sm text-gray-900">{approval.agent_name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <FileText className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">Action Type</p>
                <p className="text-sm text-gray-900">{getActionTypeDisplay(approval.action_type)}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <Clock className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">Requested</p>
                <p className="text-sm text-gray-900">
                  {new Date(approval.created_at || Date.now()).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
          
          {/* Reason */}
          {approval.reason && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Reason</h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <p className="text-sm text-yellow-800">{approval.reason}</p>
              </div>
            </div>
          )}
          
          {/* Content Preview */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Content Preview</h3>
            <div className="bg-gray-50 border rounded-md p-4 max-h-64 overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                {formatContent(approval.content)}
              </pre>
            </div>
          </div>
          
          {/* Feedback Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Feedback (Optional)
            </label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Provide feedback, instructions, or reasons for your decision..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={isProcessing}
            />
          </div>
        </div>
        
        {/* Actions */}
        <div className="border-t bg-gray-50 px-6 py-4">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleResponse('approve')}
              disabled={isProcessing}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Check className="h-4 w-4 mr-2" />
              {isProcessing ? 'Processing...' : 'Approve'}
            </button>
            
            <button
              onClick={() => handleResponse('deny')}
              disabled={isProcessing}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <X className="h-4 w-4 mr-2" />
              Deny
            </button>
            
            <button
              onClick={() => handleResponse('edit')}
              disabled={isProcessing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </button>
            
            <button
              onClick={() => handleResponse('retry')}
              disabled={isProcessing}
              className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Retry
            </button>
            
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-auto"
            >
              Cancel
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-3">
            💡 <strong>Tip:</strong> Approve to continue, Deny to stop, Edit to modify, or Retry to attempt again with different parameters.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ApprovalModal