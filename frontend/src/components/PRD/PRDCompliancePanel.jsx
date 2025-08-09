import { useState, useEffect } from 'react'
import { Shield, CheckCircle, AlertTriangle, Activity, BarChart3 } from 'lucide-react'
import HITLApprovalPanel from '../HITL/HITLApprovalPanel'
import InstagramCompliancePanel from '../Instagram/InstagramCompliancePanel'
import HubSpotPanel from '../CRM/HubSpotPanel'
import prdApi from '../../lib/prd-api'

const PRDCompliancePanel = () => {
  const [systemHealth, setSystemHealth] = useState(null)
  const [queueMetrics, setQueueMetrics] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchSystemHealth()
    fetchQueueMetrics()
  }, [])

  const fetchSystemHealth = async () => {
    try {
      const data = await prdApi.getSystemHealth()
      setSystemHealth(data)
    } catch (error) {
      console.error('Failed to fetch system health:', error)
    }
  }

  const fetchQueueMetrics = async () => {
    try {
      const data = await prdApi.getQueueMetrics()
      setQueueMetrics(data)
    } catch (error) {
      console.error('Failed to fetch queue metrics:', error)
    }
  }

  const SystemHealthOverview = () => {
    if (!systemHealth) return null

    const getStatusColor = (status) => {
      switch (status) {
        case 'healthy':
        case 'implemented':
          return 'text-green-600 bg-green-100'
        case 'degraded':
        case 'warning':
          return 'text-yellow-600 bg-yellow-100'
        case 'error':
        case 'unhealthy':
          return 'text-red-600 bg-red-100'
        default:
          return 'text-gray-600 bg-gray-100'
      }
    }

    return (
      <div className="space-y-6">
        {/* Overall Status */}
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemHealth.overall_status)}`}>
              {systemHealth.overall_status.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(systemHealth.components || {}).map(([component, data]) => (
              <div key={component} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900 capitalize">{component}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(data.status)}`}>
                    {data.status}
                  </span>
                </div>
                {data.error && (
                  <p className="text-sm text-red-600">{data.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* PRD Compliance Status */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">PRD Compliance Status</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(systemHealth.prd_compliance || {}).map(([feature, status]) => (
              <div key={feature} className="flex items-center justify-between p-3 border rounded">
                <span className="text-sm font-medium text-gray-700">
                  {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <div className="flex items-center space-x-2">
                  {status === 'implemented' ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  )}
                  <span className={`text-xs font-medium ${getStatusColor(status)}`}>
                    {status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Queue Metrics */}
        {queueMetrics && (
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Queue System Metrics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(queueMetrics.queues || {}).map(([queueType, metrics]) => (
                <div key={queueType} className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2 capitalize">
                    {queueType.replace(/_/g, ' ')} Queue
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Pending:</span>
                      <span className="font-medium">{metrics.pending || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delayed:</span>
                      <span className="font-medium">{metrics.delayed || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Failed:</span>
                      <span className="font-medium text-red-600">{metrics.failed || 0}</span>
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

  const TabButton = ({ id, label, icon: Icon, isActive, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'bg-blue-600 text-white'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      }`}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <SystemHealthOverview />
      case 'hitl':
        return <HITLApprovalPanel />
      case 'instagram':
        return <InstagramCompliancePanel />
      case 'hubspot':
        return <HubSpotPanel />
      default:
        return <SystemHealthOverview />
    }
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Shield className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">PRD Compliance Dashboard</h2>
        </div>
        
        <button
          onClick={() => {
            fetchSystemHealth()
            fetchQueueMetrics()
          }}
          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
        >
          Refresh All
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 mb-6 p-1 bg-gray-100 rounded-lg">
        <TabButton
          id="overview"
          label="System Overview"
          icon={Activity}
          isActive={activeTab === 'overview'}
          onClick={setActiveTab}
        />
        <TabButton
          id="hitl"
          label="HITL Approvals"
          icon={CheckCircle}
          isActive={activeTab === 'hitl'}
          onClick={setActiveTab}
        />
        <TabButton
          id="instagram"
          label="Instagram Compliance"
          icon={Shield}
          isActive={activeTab === 'instagram'}
          onClick={setActiveTab}
        />
        <TabButton
          id="hubspot"
          label="HubSpot CRM"
          icon={BarChart3}
          isActive={activeTab === 'hubspot'}
          onClick={setActiveTab}
        />
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {renderTabContent()}
      </div>
    </div>
  )
}

export default PRDCompliancePanel