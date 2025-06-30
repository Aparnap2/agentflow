import { useState, useEffect } from 'react'
import { DollarSign, Users, TrendingUp, Target, AlertTriangle, CheckCircle } from 'lucide-react'
import { apiMethods } from '../lib/api'
import MetricCard from '../components/Dashboard/MetricCard'
import ChartContainer from '../components/Dashboard/ChartContainer'

const DashboardPage = () => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])
  
  const fetchDashboardData = async () => {
    try {
      const [comprehensiveReport, agentsStatus, outputs] = await Promise.all([
        apiMethods.getComprehensiveReport?.() || Promise.resolve({}),
        apiMethods.getAgentsStatus(),
        apiMethods.getOutputs()
      ])
      
      setDashboardData({
        report: comprehensiveReport,
        agents: agentsStatus,
        outputs: outputs
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }
  
  const executiveSummary = dashboardData?.report?.executive_summary || {}
  const projectHealth = executiveSummary.project_health || {}
  const keyMetrics = executiveSummary.key_metrics || {}
  
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Executive Dashboard</h1>
        <p className="text-gray-600">Real-time project health and key performance indicators</p>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Project Health"
          value={`${projectHealth.overall_score || 75}%`}
          change="↑ 5% from last week"
          trend="up"
          icon={Target}
          color="green"
        />
        <MetricCard
          title="Market Opportunity"
          value={keyMetrics.market_opportunity || "$2.5B TAM"}
          change="Total addressable market"
          icon={TrendingUp}
          color="blue"
        />
        <MetricCard
          title="Funding Runway"
          value={keyMetrics.funding_runway || "18 months"}
          change="Based on current burn rate"
          icon={DollarSign}
          color="yellow"
        />
        <MetricCard
          title="Confidence Level"
          value={`${Math.round((projectHealth.confidence || 0.75) * 100)}%`}
          change="Overall system confidence"
          trend="up"
          icon={CheckCircle}
          color="green"
        />
      </div>
      
      {/* Agent Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartContainer title="Agent Status">
          <div className="space-y-3">
            {Object.entries(dashboardData?.agents || {}).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <span className="font-medium text-gray-900">{name}</span>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    status.status === 'completed' ? 'bg-green-100 text-green-700' :
                    status.status === 'working' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {status.status}
                  </span>
                  {status.outputs_ready && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </ChartContainer>
        
        <ChartContainer title="Risk Assessment">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-md">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <span className="text-sm font-medium text-red-900">High Priority</span>
              </div>
              <span className="text-sm text-red-700">Market validation</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-md">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium text-yellow-900">Medium Priority</span>
              </div>
              <span className="text-sm text-yellow-700">Technical execution</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-md">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-green-900">Low Risk</span>
              </div>
              <span className="text-sm text-green-700">Team formation</span>
            </div>
          </div>
        </ChartContainer>
      </div>
      
      {/* Progress Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartContainer title="Milestone Progress" className="lg:col-span-2">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-700">Vision Definition</span>
                <span className="text-green-600">100%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{width: '100%'}}></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-700">Strategic Planning</span>
                <span className="text-blue-600">85%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{width: '85%'}}></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-700">MVP Development</span>
                <span className="text-yellow-600">25%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{width: '25%'}}></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-700">Go-to-Market</span>
                <span className="text-gray-600">10%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-gray-400 h-2 rounded-full" style={{width: '10%'}}></div>
              </div>
            </div>
          </div>
        </ChartContainer>
        
        <ChartContainer title="Next Actions">
          <div className="space-y-3">
            {(executiveSummary.critical_actions || [
              "Complete MVP development",
              "Finalize legal documentation", 
              "Launch marketing campaigns",
              "Establish sales processes"
            ]).map((action, index) => (
              <div key={index} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-md">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-700">{action}</span>
              </div>
            ))}
          </div>
        </ChartContainer>
      </div>
    </div>
  )
}

export default DashboardPage