import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity, 
  AlertTriangle, 
  ArrowRight, 
  Clock, 
  GitBranch,
  Network,
  RefreshCw,
  Users,
  Zap
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  ConnectionMode,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';

interface TaskFlowNode {
  id: string;
  agent_name: string;
  task_type: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  start_time?: string;
  end_time?: string;
  dependencies: string[];
  metadata: Record<string, any>;
}

interface TaskFlowEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: 'dependency' | 'communication' | 'handoff';
  metadata: Record<string, any>;
}

interface PriorityConflict {
  id: string;
  agents_involved: string[];
  conflict_type: string;
  description: string;
  priority_level: 'high' | 'medium' | 'low';
  created_at: string;
  status: 'active' | 'resolved' | 'escalated';
  resolution?: Record<string, any>;
}

interface TaskFlowData {
  graph: {
    nodes: TaskFlowNode[];
    edges: TaskFlowEdge[];
    metadata: Record<string, any>;
  };
  conflicts: PriorityConflict[];
  statistics: Record<string, any>;
  timestamp: string;
}

const nodeStatusColors = {
  pending: '#fbbf24',
  active: '#3b82f6',
  completed: '#10b981',
  failed: '#ef4444',
  idle: '#6b7280'
};

const edgeTypeColors = {
  dependency: '#ef4444',
  communication: '#3b82f6',
  handoff: '#10b981'
};

const conflictPriorityColors = {
  high: 'bg-red-100 border-red-300 text-red-800',
  medium: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  low: 'bg-blue-100 border-blue-300 text-blue-800'
};

export const TaskFlowVisualization: React.FC = () => {
  const [flowData, setFlowData] = useState<TaskFlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConflict, setSelectedConflict] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // WebSocket connection for real-time updates
  const { data: wsData, isConnected } = useWebSocket('/api/task-flow/ws');

  // Fetch task flow data
  const fetchTaskFlow = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/task-flow/current');
      if (!response.ok) throw new Error('Failed to fetch task flow');
      
      const data = await response.json();
      setFlowData(data);
      updateFlowVisualization(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Handle WebSocket updates
  useEffect(() => {
    if (wsData && wsData.type === 'task_flow') {
      setFlowData(wsData.data);
      updateFlowVisualization(wsData.data);
    } else if (wsData && wsData.type === 'conflict_resolved') {
      // Refresh data when conflicts are resolved
      fetchTaskFlow();
    }
  }, [wsData]);

  // Convert backend data to ReactFlow format
  const updateFlowVisualization = useCallback((data: TaskFlowData) => {
    if (!data.graph) return;

    // Convert nodes
    const flowNodes: Node[] = data.graph.nodes.map((node, index) => ({
      id: node.id,
      type: 'default',
      position: { 
        x: (index % 4) * 250, 
        y: Math.floor(index / 4) * 150 
      },
      data: {
        label: (
          <div className="p-2 text-center">
            <div className="font-semibold text-sm">{node.agent_name}</div>
            <div className="text-xs text-gray-600">{node.task_type}</div>
            <div className="mt-1">
              <Badge 
                variant="outline" 
                className="text-xs"
                style={{ 
                  backgroundColor: nodeStatusColors[node.status],
                  color: 'white',
                  borderColor: nodeStatusColors[node.status]
                }}
              >
                {node.status}
              </Badge>
            </div>
            {node.metadata.active_jobs > 0 && (
              <div className="text-xs mt-1 text-blue-600">
                {node.metadata.active_jobs} active
              </div>
            )}
          </div>
        )
      },
      style: {
        background: 'white',
        border: `2px solid ${nodeStatusColors[node.status]}`,
        borderRadius: '8px',
        width: 180,
        height: 100
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left
    }));

    // Convert edges
    const flowEdges: Edge[] = data.graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.relationship_type === 'communication',
      style: {
        stroke: edgeTypeColors[edge.relationship_type] || '#6b7280',
        strokeWidth: 2
      },
      label: edge.relationship_type,
      labelStyle: {
        fontSize: '10px',
        fontWeight: 'bold'
      }
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [setNodes, setEdges]);

  // Resolve conflict
  const resolveConflict = async (conflictId: string, resolution: Record<string, any>) => {
    try {
      const response = await fetch(`/api/task-flow/conflicts/${conflictId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resolution)
      });
      
      if (!response.ok) throw new Error('Failed to resolve conflict');
      
      // Refresh data
      await fetchTaskFlow();
      setSelectedConflict(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve conflict');
    }
  };

  // Initial load
  useEffect(() => {
    fetchTaskFlow();
  }, []);

  if (loading && !flowData) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading task flow...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Error loading task flow: {error}
          <Button onClick={fetchTaskFlow} className="ml-4" size="sm">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!flowData) return null;

  const activeConflicts = flowData.conflicts.filter(c => c.status === 'active');
  const highPriorityConflicts = activeConflicts.filter(c => c.priority_level === 'high');

  return (
    <div className="space-y-6">
      {/* Header with statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Agents</p>
                <p className="text-2xl font-bold">{flowData.statistics.active_agents || 0}</p>
              </div>
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Communications</p>
                <p className="text-2xl font-bold">{flowData.statistics.total_communications || 0}</p>
              </div>
              <Network className="w-6 h-6 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Conflicts</p>
                <p className="text-2xl font-bold text-red-600">{activeConflicts.length}</p>
              </div>
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Connection</p>
                <p className="text-sm font-medium">
                  {isConnected ? 'Real-time' : 'Offline'}
                </p>
              </div>
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* High priority conflicts alert */}
      {highPriorityConflicts.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {highPriorityConflicts.length} high-priority conflicts require immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {/* Main content tabs */}
      <Tabs defaultValue="flow" className="w-full">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="flow">Flow Diagram</TabsTrigger>
            <TabsTrigger value="conflicts">
              Conflicts ({activeConflicts.length})
            </TabsTrigger>
            <TabsTrigger value="statistics">Statistics</TabsTrigger>
          </TabsList>
          <Button onClick={fetchTaskFlow} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        <TabsContent value="flow" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <GitBranch className="w-5 h-5 mr-2" />
                Agent Task Flow
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-96 border rounded-lg">
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  connectionMode={ConnectionMode.Loose}
                  fitView
                  attributionPosition="bottom-left"
                >
                  <Background />
                  <Controls />
                </ReactFlow>
              </div>
              
              {/* Legend */}
              <div className="mt-4 flex flex-wrap gap-4 text-sm">
                <div className="flex items-center">
                  <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: edgeTypeColors.dependency }} />
                  <span>Dependencies</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: edgeTypeColors.communication }} />
                  <span>Communications</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: edgeTypeColors.handoff }} />
                  <span>Handoffs</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conflicts" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {activeConflicts.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center text-gray-500">
                    <Zap className="w-12 h-12 mx-auto mb-4 text-green-500" />
                    <p>No active conflicts detected</p>
                    <p className="text-sm">All agents are working harmoniously</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              activeConflicts.map((conflict) => (
                <Card key={conflict.id} className="border-l-4 border-l-red-500">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{conflict.conflict_type}</CardTitle>
                      <Badge className={conflictPriorityColors[conflict.priority_level]}>
                        {conflict.priority_level} priority
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <p className="text-gray-700">{conflict.description}</p>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-1" />
                          <span>Agents: {conflict.agents_involved.join(', ')}</span>
                        </div>
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>Created: {new Date(conflict.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => resolveConflict(conflict.id, { resolution_type: 'auto_resolve' })}
                          size="sm"
                          variant="outline"
                        >
                          Auto Resolve
                        </Button>
                        <Button
                          onClick={() => setSelectedConflict(conflict.id)}
                          size="sm"
                          variant="outline"
                        >
                          Manual Resolution
                        </Button>
                        <Button
                          onClick={() => resolveConflict(conflict.id, { resolution_type: 'escalate' })}
                          size="sm"
                          variant="destructive"
                        >
                          Escalate
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="statistics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Communication Types</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(flowData.statistics.communication_types || {}).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="capitalize">{type.replace(/_/g, ' ')}</span>
                      <Badge variant="secondary">{String(count)}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Agent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(flowData.statistics.agent_activity || {}).map(([agent, activity]: [string, any]) => (
                    <div key={agent} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{agent}</span>
                        <Badge variant={activity.status === 'active' ? 'default' : 'secondary'}>
                          {activity.status}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 ml-4">
                        Active: {activity.active_jobs || 0} | Pending: {activity.pending_jobs || 0}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Flow Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Total Nodes:</span>
                  <div className="font-medium">{flowData.graph.metadata.total_nodes || 0}</div>
                </div>
                <div>
                  <span className="text-gray-600">Total Edges:</span>
                  <div className="font-medium">{flowData.graph.metadata.total_edges || 0}</div>
                </div>
                <div>
                  <span className="text-gray-600">Generated At:</span>
                  <div className="font-medium">
                    {flowData.graph.metadata.generated_at ? 
                      new Date(flowData.graph.metadata.generated_at).toLocaleTimeString() : 
                      'N/A'
                    }
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">Last Updated:</span>
                  <div className="font-medium">
                    {new Date(flowData.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};