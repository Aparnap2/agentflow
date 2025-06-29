import { useState, useEffect } from 'react'
import { Users, Settings, Brain, DollarSign, TrendingUp, Scale, MessageSquare, Zap } from 'lucide-react'
import api from '../lib/api'

const VirtualOfficePage = () => {
  const [agents, setAgents] = useState({})
  const [agentConfigs, setAgentConfigs] = useState({})
  const [selectedAgent, setSelectedAgent] = useState(null)

  const agentProfiles = {
    Cofounder: {
      icon: Brain,
      color: 'purple',
      role: 'Vision & Strategy',
      description: 'Captures vision, defines goals, identifies market opportunities',
      personality: 'Conversational and strategic',
      expertise: ['Strategy', 'Market Analysis', 'Vision Setting', 'User Research']
    },
    Manager: {
      icon: Users,
      color: 'blue',
      role: 'Project Management',
      description: 'Breaks down vision into workstreams and assigns tasks',
      personality: 'Organized and tactical',
      expertise: ['Project Management', 'Workflow Design', 'Resource Allocation', 'Timeline Planning']
    },
    Product: {
      icon: Zap,
      color: 'green',
      role: 'Product Development',
      description: 'Defines MVP, creates user personas, designs features',
      personality: 'User-focused and analytical',
      expertise: ['Product Strategy', 'User Experience', 'Feature Design', 'Market Research']
    },
    Finance: {
      icon: DollarSign,
      color: 'yellow',
      role: 'Financial Planning',
      description: 'Creates financial models, analyzes ROI, plans budgets',
      personality: 'Data-driven and precise',
      expertise: ['Financial Modeling', 'ROI Analysis', 'Budget Planning', 'Pricing Strategy']
    },
    Marketing: {
      icon: TrendingUp,
      color: 'pink',
      role: 'Growth & Marketing',
      description: 'Develops content strategy, plans campaigns, analyzes market',
      personality: 'Creative and growth-focused',
      expertise: ['Content Strategy', 'SEO', 'Social Media', 'Campaign Planning']
    },
    Legal: {
      icon: Scale,
      color: 'gray',
      role: 'Legal & Compliance',
      description: 'Drafts legal documents, ensures compliance, manages risk',
      personality: 'Thorough and risk-aware',
      expertise: ['Legal Documentation', 'Compliance', 'Risk Management', 'Contract Review']
    }
  }

  useEffect(() => {
    fetchAgentStatus()
    loadAgentConfigs()
  }, [])

  const fetchAgentStatus = async () => {
    try {
      const status = await api.getAgentsStatus()
      setAgents(status)
    } catch (error) {
      console.error('Failed to fetch agent status:', error)
    }
  }

  const loadAgentConfigs = () => {
    // Fallback default configs
    const configs = {}
    Object.keys(agentProfiles).forEach(agent => {
      configs[agent] = {
        approvalMode: 'manual',
        priority: 'medium',
        temperature: 0.7,
        maxRetries: 3,
        confidenceThreshold: 0.8,
        enabled: true
      }
    })
    setAgentConfigs(configs)
  }

  const updateAgentConfig = (agent, key, value) => {
    setAgentConfigs(prev => ({
      ...prev,
      [agent]: { ...prev[agent], [key]: value }
    }))
  }

  const saveConfiguration = async () => {
    try {
      await api.updateAgentConfigs(agentConfigs)
      alert('Configuration saved successfully!')
    } catch (error) {
      console.error('Failed to save configuration:', error)
      alert('Failed to save configuration')
    }
  }

  // Load existing configs on mount
  useEffect(() => {
    const loadConfigs = async () => {
      try {
        const configs = await api.getAgentConfigs()
        setAgentConfigs(configs)
      } catch (error) {
        console.error('Failed to load configs:', error)
      }
    }
    loadConfigs()
  }, [])

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Virtual AI Office</h1>
        <p className="text-gray-600">Customize your AI team members and their behaviors</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Agent Grid */}
        <div className="lg:col-span-3">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(agentProfiles).map(([name, profile]) => {
              const Icon = profile.icon
              const config = agentConfigs[name] || {}
              const status = agents[name]?.status || 'idle'
              
              return (
                <div
                  key={name}
                  className={`bg-white rounded-lg shadow-sm border-2 cursor-pointer transition-all hover:shadow-md ${
                    selectedAgent === name ? `border-${profile.color}-500` : 'border-gray-200'
                  }`}
                  onClick={() => setSelectedAgent(name)}
                >
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-lg bg-${profile.color}-100`}>
                        <Icon className={`h-6 w-6 text-${profile.color}-600`} />
                      </div>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        status === 'running' ? 'bg-green-100 text-green-700' :
                        status === 'idle' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {status}
                      </div>
                    </div>
                    
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{name}</h3>
                    <p className={`text-sm font-medium text-${profile.color}-600 mb-2`}>{profile.role}</p>
                    <p className="text-sm text-gray-600 mb-4">{profile.description}</p>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Approval Mode</span>
                        <span className={`px-2 py-1 rounded ${
                          config.approvalMode === 'auto' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                        }`}>
                          {config.approvalMode || 'manual'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Priority</span>
                        <span className="text-gray-700 capitalize">{config.priority || 'medium'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="lg:col-span-1">
          {selectedAgent ? (
            <div className="bg-white rounded-lg shadow-sm border p-6 sticky top-6">
              <div className="flex items-center mb-4">
                <Settings className="h-5 w-5 text-gray-600 mr-2" />
                <h3 className="font-semibold text-gray-900">{selectedAgent} Settings</h3>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Approval Mode
                  </label>
                  <select
                    value={agentConfigs[selectedAgent]?.approvalMode || 'manual'}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'approvalMode', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="manual">Manual Approval</option>
                    <option value="auto">Auto Approve</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority Level
                  </label>
                  <select
                    value={agentConfigs[selectedAgent]?.priority || 'medium'}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'priority', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Creativity (Temperature)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={agentConfigs[selectedAgent]?.temperature || 0.7}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'temperature', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Conservative</span>
                    <span>{agentConfigs[selectedAgent]?.temperature || 0.7}</span>
                    <span>Creative</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confidence Threshold
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1"
                    step="0.1"
                    value={agentConfigs[selectedAgent]?.confidenceThreshold || 0.8}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'confidenceThreshold', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-xs text-gray-500 mt-1 text-center">
                    {Math.round((agentConfigs[selectedAgent]?.confidenceThreshold || 0.8) * 100)}%
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Retries
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={agentConfigs[selectedAgent]?.maxRetries || 3}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'maxRetries', parseInt(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={agentConfigs[selectedAgent]?.enabled !== false}
                    onChange={(e) => updateAgentConfig(selectedAgent, 'enabled', e.target.checked)}
                    className="h-4 w-4 text-primary-600 border-gray-300 rounded"
                  />
                  <label htmlFor="enabled" className="ml-2 text-sm text-gray-700">
                    Agent Enabled
                  </label>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t">
                <h4 className="font-medium text-gray-900 mb-2">Agent Profile</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <p><span className="font-medium">Personality:</span> {agentProfiles[selectedAgent]?.personality}</p>
                  <div>
                    <span className="font-medium">Expertise:</span>
                    <ul className="list-disc list-inside ml-2 mt-1">
                      {agentProfiles[selectedAgent]?.expertise.map((skill, i) => (
                        <li key={i}>{skill}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="font-medium text-gray-900 mb-2">Select an Agent</h3>
              <p className="text-sm text-gray-600">Click on an agent to customize their settings</p>
            </div>
          )}
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={saveConfiguration}
          className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          Save Configuration
        </button>
      </div>
    </div>
  )
}

export default VirtualOfficePage