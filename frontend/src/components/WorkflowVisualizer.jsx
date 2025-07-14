import { useState, useEffect, useCallback } from 'react'
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  addEdge
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Brain, Users, Target, DollarSign, Megaphone, Scale } from 'lucide-react'
import api from '../lib/api'

const AgentNode = ({ data }) => {
  const Icon = data.icon
  const statusColor = {
    idle: 'bg-gray-100 border-gray-300',
    working: 'bg-blue-100 border-blue-500 animate-pulse',
    completed: 'bg-green-100 border-green-500',
    error: 'bg-red-100 border-red-500'
  }[data.status] || 'bg-gray-100 border-gray-300'

  return (
    <div className={`px-4 py-3 shadow-md rounded-md border-2 ${statusColor} min-w-[120px]`}>
      <div className="flex items-center space-x-2">
        <Icon className="h-5 w-5" />
        <div>
          <div className="font-bold text-sm">{data.label}</div>
          <div className="text-xs text-gray-600">{data.status}</div>
        </div>
      </div>
    </div>
  )
}

const nodeTypes = {
  agentNode: AgentNode
}

const WorkflowVisualizer = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [agentStatuses, setAgentStatuses] = useState({})

  const agentConfig = {
    Cofounder: { icon: Brain, position: { x: 250, y: 50 } },
    Manager: { icon: Users, position: { x: 250, y: 150 } },
    Finance: { icon: DollarSign, position: { x: 150, y: 250 } },
    Marketing: { icon: Megaphone, position: { x: 250, y: 250 } },
    Legal: { icon: Scale, position: { x: 350, y: 250 } },
    Sales: { icon: Target, position: { x: 450, y: 250 } }
  }

  useEffect(() => {
    fetchAgentStatuses()
    const interval = setInterval(fetchAgentStatuses, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchAgentStatuses = async () => {
    try {
      const statuses = await api.getAgentsStatus()
      setAgentStatuses(statuses)
      updateNodes(statuses)
    } catch (error) {
      console.error('Failed to fetch agent statuses:', error)
    }
  }

  const updateNodes = (statuses) => {
    const newNodes = Object.entries(agentConfig).map(([agentName, config]) => ({
      id: agentName,
      type: 'agentNode',
      position: config.position,
      data: {
        label: agentName,
        icon: config.icon,
        status: statuses[agentName]?.status || 'idle'
      }
    }))

    const newEdges = [
      { id: 'cofounder-manager', source: 'Cofounder', target: 'Manager', animated: true },
      { id: 'manager-finance', source: 'Manager', target: 'Finance', animated: true },
      { id: 'manager-marketing', source: 'Manager', target: 'Marketing', animated: true },
      { id: 'manager-legal', source: 'Manager', target: 'Legal', animated: true },
      { id: 'manager-sales', source: 'Manager', target: 'Sales', animated: true }
    ]

    setNodes(newNodes)
    setEdges(newEdges)
  }

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  return (
    <div className="h-96 w-full border rounded-lg bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  )
}

export default WorkflowVisualizer