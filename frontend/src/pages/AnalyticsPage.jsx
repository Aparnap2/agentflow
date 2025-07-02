import { useState, useEffect } from 'react'
import { Brain, TrendingUp, Target, Lightbulb, BarChart3 } from 'lucide-react'
import api from '../lib/api'
import ChartContainer from '../components/Dashboard/ChartContainer'
import PredictionCard from '../components/Dashboard/PredictionCard'

const AnalyticsPage = () => {
  const [predictions, setPredictions] = useState(null)
  const [outputs, setOutputs] = useState({})
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchAnalytics()
    const interval = setInterval(fetchAnalytics, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])
  
  const fetchAnalytics = async () => {
    try {
      const [predictionsData, outputsData] = await Promise.all([
        api.getPredictions(),
        api.getOutputs()
      ])
      
      setPredictions(predictionsData)
      setOutputs(outputsData)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
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
  
  const renderSuccessFactors = () => {
    const factors = predictions?.project_success?.key_factors || []
    
    return (
      <ChartContainer title="Success Factors Analysis">
        <div className="space-y-3">
          {factors.map((factor, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-green-50 rounded-md">
              <Target className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-900">{factor}</span>
            </div>
          ))}
          {factors.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Brain className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p>Success factors analysis in progress</p>
            </div>
          )}
        </div>
      </ChartContainer>
    )
  }
  
  const renderRevenueAnalysis = () => {
    const revenueTrend = predictions?.revenue_trend || {}
    
    return (
      <ChartContainer title="Revenue Trend Analysis">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-blue-50 rounded-md text-center">
              <div className="text-2xl font-bold text-blue-600">
                {revenueTrend.growth_rate || 'N/A'}%
              </div>
              <div className="text-sm text-blue-700">Growth Rate</div>
            </div>
            <div className="p-3 bg-green-50 rounded-md text-center">
              <div className="text-2xl font-bold text-green-600">
                ${(revenueTrend.next_year_prediction || 0).toLocaleString()}
              </div>
              <div className="text-sm text-green-700">Next Year Prediction</div>
            </div>
          </div>
          
          <div className="flex items-center justify-center space-x-2 p-3 bg-gray-50 rounded-md">
            <TrendingUp className={`h-5 w-5 ${
              revenueTrend.trend === 'growing' ? 'text-green-500' : 
              revenueTrend.trend === 'stable' ? 'text-yellow-500' : 'text-red-500'
            }`} />
            <span className="font-medium capitalize">{revenueTrend.trend || 'Analyzing'} Trend</span>
          </div>
        </div>
      </ChartContainer>
    )
  }
  
  const renderMarketTiming = () => {
    const marketTiming = predictions?.market_timing || {}
    const actions = marketTiming.recommended_actions || []
    
    return (
      <ChartContainer title="Market Timing Analysis">
        <div className="space-y-4">
          <div className="text-center p-4 bg-blue-50 rounded-md">
            <div className="text-lg font-semibold text-blue-900 mb-1">
              Optimal Timing: {marketTiming.optimal_timing || 'Analyzing'}
            </div>
            <div className="text-sm text-blue-700">
              Timing Score: {marketTiming.timing_score || 'N/A'}
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Recommended Actions</h4>
            {actions.map((action, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                <span className="text-sm text-gray-700">{action}</span>
              </div>
            ))}
          </div>
        </div>
      </ChartContainer>
    )
  }
  
  const renderAgentPerformance = () => {
    const agentConfidences = []
    
    Object.entries(outputs).forEach(([filename, data]) => {
      if (filename.endsWith('.json') && data.confidence) {
        agentConfidences.push({
          agent: data.agent || filename.replace('.json', ''),
          confidence: data.confidence
        })
      }
    })
    
    return (
      <ChartContainer title="Agent Performance Analysis">
        <div className="space-y-3">
          {agentConfidences.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
              <span className="font-medium text-gray-900">{item.agent}</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      item.confidence > 0.8 ? 'bg-green-500' : 
                      item.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${item.confidence * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium text-gray-600">
                  {Math.round(item.confidence * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Predictive Analytics</h1>
        <p className="text-gray-600">AI-powered insights and recommendations for your project</p>
      </div>
      
      {/* Main Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <PredictionCard
          title="Project Success Probability"
          prediction={`${Math.round((predictions?.project_success?.success_probability || 0.75) * 100)}%`}
          confidence={predictions?.project_success?.confidence_level || 'medium'}
          recommendations={predictions?.project_success?.recommendations || []}
        />
        <PredictionCard
          title="Revenue Growth Trend"
          prediction={predictions?.revenue_trend?.trend || 'Growing'}
          confidence="medium"
          recommendations={[
            `Growth rate: ${predictions?.revenue_trend?.growth_rate || 25}%`,
            `Next year: $${(predictions?.revenue_trend?.next_year_prediction || 0).toLocaleString()}`
          ]}
        />
        <PredictionCard
          title="Market Entry Timing"
          prediction={predictions?.market_timing?.optimal_timing || 'Soon'}
          confidence="high"
          recommendations={predictions?.market_timing?.recommended_actions || []}
        />
      </div>
      
      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderSuccessFactors()}
        {renderRevenueAnalysis()}
        {renderMarketTiming()}
        {renderAgentPerformance()}
      </div>
    </div>
  )
}

export default AnalyticsPage