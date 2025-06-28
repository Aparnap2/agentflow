import { useState, useEffect } from 'react'
import { GitBranch, Search, Filter, Download } from 'lucide-react'
import { apiMethods } from '../lib/api'

const GraphPage = () => {
  const [graphData, setGraphData] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchGraphData()
  }, [])
  
  const fetchGraphData = async () => {
    try {
      const data = await apiMethods.getMemoryGraph()
      setGraphData(data)
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const exportGraph = async () => {
    try {
      await apiMethods.exportMemory()
      alert('Graph exported successfully!')
    } catch (error) {
      console.error('Failed to export graph:', error)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }
  
  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Memory Graph</h1>
          <p className="text-gray-600">Visualize agent memory and context relationships</p>
        </div>
        <button onClick={exportGraph} className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          <Download className="h-4 w-4 mr-2" />
          Export GraphML
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex-1 relative">
            <Search className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="flex items-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </button>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <GitBranch className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Interactive Graph View</h3>
              <p className="text-gray-600">Graph visualization would be rendered here using D3.js or similar</p>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Graph Statistics</h3>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Total Agents</p>
                <p className="text-2xl font-bold text-gray-900">{graphData?.agents?.length || 0}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Memory Nodes</p>
                <p className="text-2xl font-bold text-gray-900">
                  {graphData?.agents?.reduce((sum, agent) => sum + agent.private_memories + agent.shared_contributions, 0) || 0}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Recent Activity</p>
                <p className="text-2xl font-bold text-gray-900">{graphData?.recent_shared?.length || 0}</p>
              </div>
            </div>
            
            {selectedNode && (
              <div className="mt-6">
                <h3 className="font-semibold text-gray-900 mb-4">Node Details</h3>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <pre className="text-sm text-blue-800 whitespace-pre-wrap">
                    {JSON.stringify(selectedNode, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphPage