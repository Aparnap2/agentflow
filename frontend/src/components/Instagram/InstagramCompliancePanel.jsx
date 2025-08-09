import { useState, useEffect } from 'react'
import { Instagram, Clock, Shield, AlertTriangle, CheckCircle, MessageSquare } from 'lucide-react'
import prdApi from '../../lib/prd-api'

const InstagramCompliancePanel = () => {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchComplianceDashboard()
  }, [])

  const fetchComplianceDashboard = async () => {
    try {
      const data = await prdApi.getComplianceDashboard()
      setDashboard(data)
    } catch (error) {
      console.error('Failed to fetch compliance dashboard:', error)
    }
  }

  const checkConversationCompliance = async (conversationId) => {
    try {
      const data = await prdApi.getComplianceStatus(conversationId)
      return data
    } catch (error) {
      console.error('Failed to check compliance:', error)
      return null
    }
  }

  const sendCompliantDM = async (conversationId, userId, message, messageType = 'auto_response') => {
    setLoading(true)
    try {
      const result = await prdApi.sendCompliantDM(conversationId, userId, message, messageType)
      
      if (result.success) {
        console.log('DM sent successfully')
        fetchComplianceDashboard() // Refresh dashboard
      } else {
        console.error('DM blocked:', result.reason)
      }
      
      return result
    } catch (error) {
      console.error('Failed to send DM:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  const ComplianceStatusBadge = ({ status, windowStatus }) => {
    const getStatusColor = () => {
      if (status === 'compliant' && windowStatus === 'active') {
        return 'bg-green-100 text-green-800'
      } else if (windowStatus === 'expired_human_tag_available') {
        return 'bg-yellow-100 text-yellow-800'
      } else if (windowStatus === 'expired') {
        return 'bg-red-100 text-red-800'
      }
      return 'bg-gray-100 text-gray-800'
    }

    const getStatusText = () => {
      if (status === 'compliant' && windowStatus === 'active') {
        return 'Active Window'
      } else if (windowStatus === 'expired_human_tag_available') {
        return 'Human Tag Available'
      } else if (windowStatus === 'expired') {
        return 'Window Expired'
      }
      return 'Unknown'
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
        {getStatusText()}
      </span>
    )
  }

  const ComplianceDashboard = () => {
    if (!dashboard) return null

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <MessageSquare className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Conversations</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboard.compliance_summary?.total_conversations || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Active Windows</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboard.compliance_summary?.active_windows || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Expired Windows</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboard.compliance_summary?.expired_windows || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-red-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Blocked Responses</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboard.compliance_summary?.blocked_responses || 0}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const ConversationTester = () => {
    const [testData, setTestData] = useState({
      conversationId: '',
      userId: '',
      message: '',
      messageType: 'auto_response'
    })
    const [testResult, setTestResult] = useState(null)

    const handleTest = async () => {
      if (!testData.conversationId || !testData.userId || !testData.message) {
        return
      }

      // First check compliance
      const complianceStatus = await checkConversationCompliance(testData.conversationId)
      
      if (complianceStatus) {
        setTestResult({
          compliance: complianceStatus,
          sent: false
        })

        // If compliant, optionally send the message
        if (complianceStatus.action_allowed) {
          const sendResult = await sendCompliantDM(
            testData.conversationId,
            testData.userId,
            testData.message,
            testData.messageType
          )
          setTestResult(prev => ({
            ...prev,
            sent: sendResult.success,
            sendResult
          }))
        }
      }
    }

    return (
      <div className="bg-white rounded-lg border p-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test DM Compliance</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <input
            type="text"
            placeholder="Conversation ID"
            value={testData.conversationId}
            onChange={(e) => setTestData(prev => ({...prev, conversationId: e.target.value}))}
            className="px-3 py-2 border rounded-md text-sm"
          />
          <input
            type="text"
            placeholder="User ID"
            value={testData.userId}
            onChange={(e) => setTestData(prev => ({...prev, userId: e.target.value}))}
            className="px-3 py-2 border rounded-md text-sm"
          />
        </div>

        <div className="mb-4">
          <textarea
            placeholder="Message to send..."
            value={testData.message}
            onChange={(e) => setTestData(prev => ({...prev, message: e.target.value}))}
            className="w-full px-3 py-2 border rounded-md text-sm"
            rows={3}
          />
        </div>

        <div className="flex items-center space-x-4 mb-4">
          <select
            value={testData.messageType}
            onChange={(e) => setTestData(prev => ({...prev, messageType: e.target.value}))}
            className="px-3 py-2 border rounded-md text-sm"
          >
            <option value="auto_response">Auto Response</option>
            <option value="human_response">Human Response</option>
            <option value="human_agent_tag">Human-Agent Tag</option>
            <option value="promotional">Promotional</option>
          </select>

          <button
            onClick={handleTest}
            disabled={loading || !testData.conversationId || !testData.userId || !testData.message}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {loading ? 'Testing...' : 'Test Compliance'}
          </button>
        </div>

        {testResult && (
          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-2">Test Results:</h4>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Compliance Status:</span>
                <ComplianceStatusBadge 
                  status={testResult.compliance.compliant ? 'compliant' : 'non-compliant'}
                  windowStatus={testResult.compliance.window_status}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Action Allowed:</span>
                <span className={`text-sm font-medium ${testResult.compliance.action_allowed ? 'text-green-600' : 'text-red-600'}`}>
                  {testResult.compliance.action_allowed ? 'Yes' : 'No'}
                </span>
              </div>

              {testResult.compliance.reason && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Reason:</span> {testResult.compliance.reason}
                </div>
              )}

              {testResult.compliance.expires_at && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Window Expires:</span> {
                    new Date(testResult.compliance.expires_at).toLocaleString()
                  }
                </div>
              )}

              {testResult.sent !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Message Sent:</span>
                  <span className={`text-sm font-medium ${testResult.sent ? 'text-green-600' : 'text-red-600'}`}>
                    {testResult.sent ? 'Success' : 'Failed'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Instagram className="h-5 w-5 text-pink-600" />
          <h2 className="text-lg font-semibold text-gray-900">Instagram DM Compliance</h2>
        </div>
        
        <button
          onClick={fetchComplianceDashboard}
          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
        >
          Refresh
        </button>
      </div>

      <ComplianceDashboard />
      <ConversationTester />

      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Rules</h3>
        
        <div className="space-y-3 text-sm">
          <div className="flex items-start space-x-2">
            <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
            <div>
              <span className="font-medium">24-Hour Response Window:</span>
              <p className="text-gray-600">Auto-responses allowed within 24 hours of user message</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-2">
            <Clock className="h-4 w-4 text-yellow-600 mt-0.5" />
            <div>
              <span className="font-medium">Human-Agent Tag:</span>
              <p className="text-gray-600">Extends response window to 7 days where supported</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-2">
            <Shield className="h-4 w-4 text-red-600 mt-0.5" />
            <div>
              <span className="font-medium">No Broadcasts Outside Window:</span>
              <p className="text-gray-600">Promotional content blocked outside compliance windows</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />
            <div>
              <span className="font-medium">Professional Accounts Only:</span>
              <p className="text-gray-600">Compliance features require Instagram Business account</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InstagramCompliancePanel