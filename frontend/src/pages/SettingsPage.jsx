import { useState, useEffect } from 'react'
import { Save, Trash2 } from 'lucide-react'
import { apiMethods } from '../lib/api'

const SettingsPage = () => {
  const [approvalSettings, setApprovalSettings] = useState({
    finance_agent: { api_calls: 'manual', memory_write: 'manual' },
    marketing_agent: { api_calls: 'auto', memory_write: 'auto' },
    legal_agent: { api_calls: 'manual', memory_write: 'manual' },
    product_agent: { api_calls: 'auto', memory_write: 'auto' },
    cofounder_agent: { api_calls: 'auto', memory_write: 'auto' },
    manager_agent: { api_calls: 'auto', memory_write: 'auto' }
  })
  const [memoryStats, setMemoryStats] = useState(null)
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    fetchMemoryStats()
  }, [])
  
  const fetchMemoryStats = async () => {
    try {
      const stats = await apiMethods.getMemoryStats()
      setMemoryStats(stats)
    } catch (error) {
      console.error('Failed to fetch memory stats:', error)
    }
  }
  
  const handleApprovalChange = (agent, setting, value) => {
    setApprovalSettings(prev => ({
      ...prev,
      [agent]: {
        ...prev[agent],
        [setting]: value
      }
    }))
  }
  
  const saveSettings = async () => {
    setLoading(true)
    try {
      // In a real implementation, this would save to backend
      console.log('Saving settings:', approvalSettings)
      alert('Settings saved successfully!')
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const clearMemory = async () => {
    if (!confirm('Are you sure? This will delete all agent memory and cannot be undone.')) return
    
    setLoading(true)
    try {
      await apiMethods.clearMemory()
      await fetchMemoryStats()
      alert('Memory cleared successfully!')
    } catch (error) {
      console.error('Failed to clear memory:', error)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure approval modes and manage system memory</p>
      </div>
      
      {/* Approval Settings */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Approval Configuration</h2>
        <p className="text-gray-600 mb-6">Control when agents require manual approval for actions</p>
        
        <div className="space-y-6">
          {Object.entries(approvalSettings).map(([agent, settings]) => (
            <div key={agent} className="border-b border-gray-200 pb-6 last:border-b-0">
              <h3 className="font-medium text-gray-900 mb-4 capitalize">
                {agent.replace('_', ' ')}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">API Calls</span>
                  <select
                    value={settings.api_calls}
                    onChange={(e) => handleApprovalChange(agent, 'api_calls', e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="auto">Auto</option>
                    <option value="manual">Manual</option>
                  </select>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Memory Write</span>
                  <select
                    value={settings.memory_write}
                    onChange={(e) => handleApprovalChange(agent, 'memory_write', e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="auto">Auto</option>
                    <option value="manual">Manual</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 pt-6 border-t">
          <button
            onClick={saveSettings}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4 mr-2" />
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
      
      {/* Memory Management */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Memory Management</h2>
        
        {memoryStats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Graph Memory</p>
              <p className="text-2xl font-bold text-gray-900">
                {memoryStats.graph_memory?.total_private_memories + memoryStats.graph_memory?.total_shared_memories || 0}
              </p>
              <p className="text-xs text-gray-500">nodes</p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Vector Memory</p>
              <p className="text-2xl font-bold text-gray-900">
                {memoryStats.vector_memory?.total_documents || 0}
              </p>
              <p className="text-xs text-gray-500">documents</p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Export Files</p>
              <p className="text-2xl font-bold text-gray-900">
                {memoryStats.exports?.available_files?.length || 0}
              </p>
              <p className="text-xs text-gray-500">files</p>
            </div>
          </div>
        )}
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <h3 className="font-medium text-red-900 mb-2">Danger Zone</h3>
          <p className="text-sm text-red-700 mb-4">
            This action will permanently delete all agent memory, shared context, and generated outputs.
          </p>
          <button
            onClick={clearMemory}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {loading ? 'Clearing...' : 'Clear All Memory'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage