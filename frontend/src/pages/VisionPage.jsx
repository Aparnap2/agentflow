import { useState, useEffect } from 'react'
import { Eye, CheckCircle, Clock } from 'lucide-react'
import { apiMethods } from '../lib/api'

const VisionPage = () => {
  const [outputs, setOutputs] = useState({})
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchOutputs()
  }, [])
  
  const fetchOutputs = async () => {
    try {
      const data = await apiMethods.getOutputs()
      console.log('Fetched outputs:', data)
      setOutputs(data)
    } catch (error) {
      console.error('Failed to fetch outputs:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const cofounderData = outputs['cofounder.json']?.data
  const managerData = outputs['manager.json']?.data
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Project Vision</h1>
        <p className="text-gray-600">
          Review and approve your refined vision and project roadmap
        </p>
      </div>
      
      {cofounderData && (
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center mb-4">
            <Eye className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Vision Statement</h2>
            <CheckCircle className="h-5 w-5 text-green-500 ml-auto" />
          </div>
          
          <div className="prose max-w-none">
            <p className="text-gray-700 mb-6">{cofounderData.vision_statement}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Target Users</h3>
                <div className="space-y-3">
                  {cofounderData.target_user_personas?.map((user, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-md">
                      <h4 className="font-medium text-gray-900">{user.name}</h4>
                      <p className="text-sm text-gray-600">{user.description}</p>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Strategic Priorities</h3>
                <ul className="space-y-2">
                  {cofounderData.strategic_priorities?.map((priority, index) => (
                    <li key={index} className="flex items-center text-gray-700">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                      <div>
                        <span className="font-medium">{priority.priority}:</span>
                        <span className="ml-1">{priority.description}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {managerData && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center mb-4">
            <Clock className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Project Roadmap</h2>
            <CheckCircle className="h-5 w-5 text-green-500 ml-auto" />
          </div>
          
          <div className="space-y-6">
            {Object.entries(managerData.project_roadmap || {}).map(([phaseKey, phase]) => (
              <div key={phaseKey} className="border-l-4 border-primary-200 pl-4">
                <h3 className="font-semibold text-gray-900">{phase.name}</h3>
                <p className="text-sm text-gray-600 mb-2">Duration: {phase.duration}</p>
                <div className="flex flex-wrap gap-2">
                  {phase.deliverables?.map((deliverable, index) => (
                    <span key={index} className="px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded-full">
                      {deliverable}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-900 mb-3">Agent Assignments</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(managerData.agent_assignments || {}).map(([agent, assignment]) => (
                <div key={agent} className="p-3 bg-gray-50 rounded-md">
                  <h4 className="font-medium text-gray-900 mb-2">{agent} Agent</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {assignment.primary_tasks?.slice(0, 2).map((task, index) => (
                      <li key={index}>• {task}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {!cofounderData && !managerData && (
        <div className="text-center py-12">
          <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Vision Data</h3>
          <p className="text-gray-600">Start a project to see your vision and roadmap here</p>
        </div>
      )}
    </div>
  )
}

export default VisionPage