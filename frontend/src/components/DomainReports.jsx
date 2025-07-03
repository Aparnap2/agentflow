import { useState, useEffect } from 'react'
import { FileText, Users, DollarSign, Megaphone, Scale, Target, Settings } from 'lucide-react'
import api from '../lib/api'
import { LoadingSpinner } from './shared'

const DomainReports = () => {
  const [reports, setReports] = useState({})
  const [selectedDomain, setSelectedDomain] = useState('marketing')
  const [loading, setLoading] = useState(true)

  const domainConfig = {
    marketing: { icon: Megaphone, color: 'pink', agent: 'Emma Rodriguez' },
    sales: { icon: Users, color: 'blue', agent: 'Lisa Wang' },
    finance: { icon: DollarSign, color: 'green', agent: 'David Park' },
    legal: { icon: Scale, color: 'gray', agent: 'Michael Thompson' },
    product: { icon: Target, color: 'purple', agent: 'Jordan Martinez' },
    operations: { icon: Settings, color: 'orange', agent: 'Ryan Foster' }
  }

  useEffect(() => {
    fetchDomainReports()
  }, [])

  const fetchDomainReports = async () => {
    try {
      const data = await api.get('/reports/domains')
      setReports(data.data || {})
    } catch (error) {
      console.error('Failed to fetch domain reports:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading domain reports..." />
  }

  const selectedReport = reports[selectedDomain]

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Domain Reports</h1>
        <p className="text-gray-600">Specialized reports from each AI agent</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Domain Tabs */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b">
              <h3 className="font-semibold text-gray-900">Domains</h3>
            </div>
            <div className="divide-y">
              {Object.entries(domainConfig).map(([domain, config]) => {
                const Icon = config.icon
                const isSelected = selectedDomain === domain
                const hasReport = reports[domain]
                
                return (
                  <button
                    key={domain}
                    onClick={() => setSelectedDomain(domain)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                      isSelected ? 'bg-primary-50 border-r-2 border-primary-500' : ''
                    }`}
                  >
                    <div className="flex items-center">
                      <Icon className={`h-5 w-5 text-${config.color}-600 mr-3`} />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 capitalize">{domain}</p>
                        <p className="text-sm text-gray-500">{config.agent}</p>
                      </div>
                      {hasReport && (
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Report Content */}
        <div className="lg:col-span-3">
          {selectedReport ? (
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{selectedReport.title}</h2>
                    <p className="text-sm text-gray-600 mt-1">By {selectedReport.agent}</p>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(selectedReport.generated_at).toLocaleString()}
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                {/* Report Sections */}
                <div className="space-y-6">
                  {Object.entries(selectedReport.sections || {}).map(([sectionKey, sectionData]) => (
                    <div key={sectionKey} className="border-l-4 border-primary-500 pl-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 capitalize">
                        {sectionKey.replace('_', ' ')}
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-md">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {typeof sectionData === 'object' 
                            ? JSON.stringify(sectionData, null, 2)
                            : sectionData
                          }
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Cross References */}
                {selectedReport.references && (
                  <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Cross References</h4>
                    <div className="space-y-1">
                      {Object.entries(selectedReport.references).map(([key, value]) => (
                        <p key={key} className="text-sm text-blue-800">
                          • {value}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Shared Data */}
                {selectedReport.shared_data && (
                  <div className="mt-6 p-4 bg-green-50 rounded-lg">
                    <h4 className="font-semibold text-green-900 mb-2">Shared Data</h4>
                    <div className="text-sm text-green-800">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(selectedReport.shared_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Available</h3>
              <p className="text-gray-600">
                The {selectedDomain} report hasn't been generated yet. 
                Start a project to see domain-specific reports.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DomainReports