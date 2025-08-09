import { useState, useEffect } from 'react'
import { FileText, Download, TrendingUp, DollarSign, Users, Shield } from 'lucide-react'
import api from '../lib/api'
import ChartContainer from '../components/Dashboard/ChartContainer'
import DomainReports from '../components/DomainReports'

const ReportsPage = () => {
  const [reports, setReports] = useState({})
  const [selectedReport, setSelectedReport] = useState('executive_dashboard')
  const [loading, setLoading] = useState(true)
  
  const reportTypes = [
    { id: 'executive_dashboard', name: 'Executive Dashboard', icon: TrendingUp },
    { id: 'marketing_intelligence', name: 'Marketing Intelligence', icon: Users },
    { id: 'financial_projections', name: 'Financial Projections', icon: DollarSign },
    { id: 'legal_compliance', name: 'Legal Compliance', icon: Shield },
    { id: 'sales_forecast', name: 'Sales Forecast', icon: TrendingUp }
  ]
  
  useEffect(() => {
    fetchReports()
  }, [])
  
  const fetchReports = async () => {
    try {
      const [comprehensive, ...specificReports] = await Promise.all([
        api.getComprehensiveReport(),
        ...reportTypes.map(type => 
          api.getSpecificReport(type.id).catch(() => null)
        )
      ])
      
      const reportsData = { comprehensive }
      reportTypes.forEach((type, index) => {
        if (specificReports[index]) {
          reportsData[type.id] = specificReports[index]
        }
      })
      
      setReports(reportsData)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const downloadReport = (reportType) => {
    const reportData = reports[reportType] || reports.comprehensive?.sections?.[reportType]
    if (reportData) {
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportType}_report.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
  
  const renderReportContent = () => {
    const reportData = reports[selectedReport] || reports.comprehensive?.sections?.[selectedReport]
    
    if (!reportData) {
      return (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Report Not Available</h3>
          <p className="text-gray-600">This report is being generated or not yet available</p>
        </div>
      )
    }
    
    return (
      <div className="space-y-6">
        {selectedReport === 'executive_dashboard' && renderExecutiveDashboard(reportData)}
        {selectedReport === 'marketing_intelligence' && renderMarketingReport(reportData)}
        {selectedReport === 'financial_projections' && renderFinancialReport(reportData)}
        {selectedReport === 'legal_compliance' && renderLegalReport(reportData)}
        {selectedReport === 'sales_forecast' && renderSalesReport(reportData)}
      </div>
    )
  }
  
  const renderExecutiveDashboard = (data) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartContainer title="KPI Dashboard">
        <div className="space-y-4">
          {Object.entries(data.kpi_dashboard || {}).map(([category, metrics]) => (
            <div key={category} className="border-b pb-3 last:border-b-0">
              <h4 className="font-medium text-gray-900 mb-2 capitalize">{category.replace('_', ' ')}</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(metrics).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key.replace('_', ' ')}</span>
                    <span className="font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
      
      <ChartContainer title="Milestone Tracking">
        <div className="space-y-3">
          {Object.entries(data.milestone_tracking || {}).map(([status, milestones]) => (
            <div key={status} className="space-y-2">
              <h4 className="font-medium text-gray-900 capitalize">{status.replace('_', ' ')}</h4>
              <div className="space-y-1">
                {(Array.isArray(milestones) ? milestones : []).map((milestone, index) => (
                  <div key={index} className="text-sm text-gray-600 pl-4 border-l-2 border-gray-200">
                    {milestone}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
    </div>
  )
  
  const renderMarketingReport = (data) => (
    <div className="space-y-6">
      <ChartContainer title="Content Strategy">
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Content Performance</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              {Object.entries(data.content_strategy?.content_performance || {}).map(([type, metrics]) => (
                <div key={type} className="text-center p-3 bg-gray-50 rounded">
                  <div className="font-medium capitalize">{type.replace('_', ' ')}</div>
                  <div className="text-gray-600 mt-1">
                    {typeof metrics === 'object' ? JSON.stringify(metrics) : metrics}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </ChartContainer>
      
      <ChartContainer title="Campaign Projections">
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(data.campaign_projections || {}).map(([key, value]) => (
            <div key={key} className="p-3 bg-gray-50 rounded">
              <div className="text-sm text-gray-600 capitalize">{key.replace('_', ' ')}</div>
              <div className="font-medium text-lg">{value}</div>
            </div>
          ))}
        </div>
      </ChartContainer>
    </div>
  )
  
  const renderFinancialReport = (data) => (
    <div className="space-y-6">
      <ChartContainer title="Revenue Model">
        <div className="space-y-4">
          {data.revenue_model?.pricing_tiers?.map((tier, index) => (
            <div key={index} className="p-3 border rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">{tier.tier}</span>
                <span className="text-lg font-bold">${tier.price}/mo</span>
              </div>
              <div className="text-sm text-gray-600 mt-1">{tier.target_segment}</div>
            </div>
          ))}
        </div>
      </ChartContainer>
      
      <ChartContainer title="Financial Projections">
        <div className="space-y-3">
          {Object.entries(data.financial_projections || {}).map(([year, projection]) => (
            <div key={year} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="font-medium capitalize">{year.replace('_', ' ')}</span>
              <div className="text-right">
                <div className="font-bold">${projection.revenue?.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Revenue</div>
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
    </div>
  )
  
  const renderLegalReport = (data) => (
    <div className="space-y-6">
      <ChartContainer title="Compliance Status">
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(data.compliance_status || {}).map(([regulation, score]) => (
            <div key={regulation} className="p-3 bg-gray-50 rounded">
              <div className="text-sm text-gray-600 uppercase">{regulation.replace('_', ' ')}</div>
              <div className="text-2xl font-bold text-green-600">{score}%</div>
            </div>
          ))}
        </div>
      </ChartContainer>
      
      <ChartContainer title="Legal Documents">
        <div className="space-y-2">
          {Object.entries(data.legal_documents || {}).map(([doc, status]) => (
            <div key={doc} className="flex justify-between items-center p-2 border rounded">
              <span className="capitalize">{doc.replace('_', ' ')}</span>
              <span className={`px-2 py-1 text-xs rounded ${
                status === 'Generated' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {status}
              </span>
            </div>
          ))}
        </div>
      </ChartContainer>
    </div>
  )
  
  const renderSalesReport = (data) => (
    <div className="space-y-6">
      <ChartContainer title="Sales Projections">
        <div className="space-y-3">
          {Object.entries(data.sales_projections?.monthly_targets || {}).slice(0, 6).map(([month, target]) => (
            <div key={month} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="capitalize">{month.replace('_', ' ')}</span>
              <div className="text-right">
                <div className="font-medium">{target.new_customers} customers</div>
                <div className="text-sm text-gray-600">${target.revenue?.toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
      
      <ChartContainer title="Customer Segments">
        <div className="space-y-3">
          {Object.entries(data.customer_segments?.segments || {}).map(([segment, details]) => (
            <div key={segment} className="p-3 border rounded">
              <div className="font-medium capitalize">{segment.replace('_', ' ')}</div>
              <div className="text-sm text-gray-600 mt-1">{details.description}</div>
              <div className="text-sm text-blue-600 mt-1">
                Conversion: {(details.conversion_potential * 100).toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </ChartContainer>
    </div>
  )
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Business Reports</h1>
        <p className="text-gray-600">Comprehensive analytics and insights from all agents</p>
      </div>
      
      {/* Domain Reports */}
      <div className="mb-12">
        <DomainReports />
      </div>
      
      {/* Legacy Reports */}
      <div className="border-t pt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Legacy Reports</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Report Navigation */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Available Reports</h3>
            <div className="space-y-2">
              {reportTypes.map((report) => {
                const Icon = report.icon
                return (
                  <button
                    key={report.id}
                    onClick={() => setSelectedReport(report.id)}
                    className={`w-full flex items-center space-x-3 p-3 rounded-md text-left transition-colors ${
                      selectedReport === report.id
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-sm font-medium">{report.name}</span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
        
        {/* Report Content */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                {reportTypes.find(r => r.id === selectedReport)?.name}
              </h2>
              <button
                onClick={() => downloadReport(selectedReport)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Download className="h-4 w-4" />
                <span>Download</span>
              </button>
            </div>
            <div className="p-6">
              {renderReportContent()}
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}

export default ReportsPage