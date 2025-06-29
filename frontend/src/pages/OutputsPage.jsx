import { useState, useEffect } from 'react'
import { FileText, Download, Eye, Calendar, TrendingUp, Users, DollarSign } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import api from '../lib/api'

const OutputsPage = () => {
  const [outputs, setOutputs] = useState({})
  const [selectedOutput, setSelectedOutput] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOutputs()
  }, [])

  const fetchOutputs = async () => {
    try {
      const data = await api.getOutputs()
      setOutputs(data)
    } catch (error) {
      console.error('Failed to fetch outputs:', error)
    } finally {
      setLoading(false)
    }
  }

  const downloadOutput = (filename, data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadAll = () => {
    const allData = {
      project_outputs: outputs,
      generated_at: new Date().toISOString()
    }
    downloadOutput('agentflow_outputs.json', allData)
  }

  const formatOutput = (data, agent) => {
    if (!data) return null

    switch (agent) {
      case 'finance':
        return <FinanceOutput data={data} />
      case 'product':
        return <ProductOutput data={data} />
      case 'marketing':
        return <MarketingOutput data={data} />
      case 'legal':
        return <LegalOutput data={data} />
      default:
        return <DefaultOutput data={data} />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Project Outputs</h1>
          <p className="text-gray-600">
            Review beautifully formatted deliverables from your AI team
          </p>
        </div>
        
        {Object.keys(outputs).length > 0 && (
          <button
            onClick={downloadAll}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Download All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">Generated Files</h2>
            </div>
            <div className="divide-y">
              {Object.entries(outputs).map(([filename, data]) => (
                <div
                  key={filename}
                  className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedOutput === filename ? 'bg-primary-50 border-r-2 border-primary-500' : ''
                  }`}
                  onClick={() => setSelectedOutput(filename)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="font-medium text-gray-900">{filename}</p>
                        <p className="text-sm text-gray-500">
                          {data.agent} Agent
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        downloadOutput(filename, data)
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                  {data.timestamp && (
                    <div className="flex items-center mt-2 text-xs text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {new Date(data.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* File Preview */}
        <div className="lg:col-span-2">
          {selectedOutput ? (
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-4 border-b flex items-center justify-between">
                <div className="flex items-center">
                  <Eye className="h-5 w-5 text-primary-600 mr-2" />
                  <h2 className="font-semibold text-gray-900">{selectedOutput}</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">
                    Confidence: {Math.round((outputs[selectedOutput].confidence || 0) * 100)}%
                  </span>
                  <button
                    onClick={() => downloadOutput(selectedOutput, outputs[selectedOutput])}
                    className="flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Download
                  </button>
                </div>
              </div>
              <div className="p-6">
                {formatOutput(outputs[selectedOutput].data, outputs[selectedOutput].agent.toLowerCase())}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a File</h3>
              <p className="text-gray-600">Choose a file from the list to preview its contents</p>
            </div>
          )}
        </div>
      </div>

      {Object.keys(outputs).length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Outputs Generated</h3>
          <p className="text-gray-600">Start a project to see generated deliverables here</p>
        </div>
      )}
    </div>
  )
}

// Specialized output formatters
const FinanceOutput = ({ data }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {data.financial_projections && Object.entries(data.financial_projections).map(([year, proj]) => (
        <div key={year} className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2">{year.replace('year_', 'Year ')}</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Revenue:</span>
              <span className="font-medium text-green-600">${proj.revenue?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Costs:</span>
              <span className="font-medium text-red-600">${proj.costs?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t pt-1">
              <span>Net:</span>
              <span className={`font-medium ${proj.net_income > 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${proj.net_income?.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
    
    {data.revenue_model?.pricing_tiers && (
      <div>
        <h3 className="text-lg font-semibold mb-3">Pricing Tiers</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.revenue_model.pricing_tiers.map((tier, index) => (
            <div key={index} className="border rounded-lg p-4">
              <h4 className="font-semibold text-gray-900">{tier.tier}</h4>
              <div className="text-2xl font-bold text-primary-600">${tier.price}/mo</div>
              <p className="text-sm text-gray-600 mt-2">{tier.target_segment}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
)

const ProductOutput = ({ data }) => (
  <div className="space-y-6">
    {data.user_personas && (
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <Users className="h-5 w-5 mr-2" />
          User Personas
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.user_personas.map((persona, index) => (
            <div key={index} className="border rounded-lg p-4">
              <h4 className="font-semibold text-gray-900">{persona.name}</h4>
              <p className="text-sm text-gray-600 mb-2">{persona.demographics}</p>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Goals:</span>
                  <ul className="list-disc list-inside ml-2">
                    {persona.goals?.map((goal, i) => <li key={i}>{goal}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
    
    {data.mvp_definition && (
      <div>
        <h3 className="text-lg font-semibold mb-3">MVP Definition</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <ReactMarkdown>{data.mvp_definition.scope}</ReactMarkdown>
        </div>
      </div>
    )}
  </div>
)

const MarketingOutput = ({ data }) => (
  <div className="space-y-6">
    <ReactMarkdown className="prose max-w-none">
      {JSON.stringify(data, null, 2)}
    </ReactMarkdown>
  </div>
)

const LegalOutput = ({ data }) => (
  <div className="space-y-6">
    <ReactMarkdown className="prose max-w-none">
      {JSON.stringify(data, null, 2)}
    </ReactMarkdown>
  </div>
)

const DefaultOutput = ({ data }) => (
  <div className="space-y-4">
    <ReactMarkdown className="prose max-w-none">
      {JSON.stringify(data, null, 2)}
    </ReactMarkdown>
  </div>
)

export default OutputsPage