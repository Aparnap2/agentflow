import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Cpu, 
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Zap
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

interface AgentPerformanceMetrics {
  tasks_completed: number;
  success_rate: number;
  avg_completion_time: number;
  current_workload: number;
  reliability_score: number;
}

interface AgentStatus {
  agent_name: string;
  status: 'active' | 'idle' | 'busy' | 'error';
  current_task?: string;
  last_activity: string;
  performance_metrics: AgentPerformanceMetrics;
  queue_status: Record<string, any>;
}

interface AgentStatusData {
  [agentName: string]: AgentStatus;
}

const statusColors = {
  active: 'bg-green-500',
  idle: 'bg-yellow-500',
  busy: 'bg-blue-500',
  error: 'bg-red-500'
};

const statusIcons = {
  active: CheckCircle,
  idle: Clock,
  busy: Activity,
  error: AlertCircle
};

export const AgentStatusDashboard: React.FC = () => {
  const [agentData, setAgentData] = useState<AgentStatusData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // WebSocket connection for real-time updates
  const { data: wsData, isConnected } = useWebSocket('/api/agent-status/ws');

  // Fetch initial agent status data
  const fetchAgentStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/agent-status/all');
      if (!response.ok) throw new Error('Failed to fetch agent status');
      
      const data = await response.json();
      setAgentData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Handle WebSocket updates
  useEffect(() => {
    if (wsData && wsData.type === 'agent_status') {
      setAgentData(wsData.data);
    }
  }, [wsData]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchAgentStatus();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAgentStatus, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusBadge = (status: string) => {
    const StatusIcon = statusIcons[status as keyof typeof statusIcons] || Activity;
    return (
      <Badge variant="outline" className={`${statusColors[status as keyof typeof statusColors]} text-white`}>
        <StatusIcon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const calculateOverallHealth = () => {
    const agents = Object.values(agentData);
    if (agents.length === 0) return 0;
    
    const healthyAgents = agents.filter(agent => 
      agent.status === 'active' || agent.status === 'idle'
    ).length;
    
    return Math.round((healthyAgents / agents.length) * 100);
  };

  const getPerformanceTrend = (metrics: AgentPerformanceMetrics) => {
    const score = metrics.success_rate * 0.4 + 
                  metrics.reliability_score * 0.4 + 
                  (metrics.tasks_completed > 0 ? 0.2 : 0);
    return score > 0.7 ? 'up' : score > 0.4 ? 'stable' : 'down';
  };

  if (loading && Object.keys(agentData).length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading agent status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center text-red-600">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>Error loading agent status: {error}</span>
          </div>
          <Button onClick={fetchAgentStatus} className="mt-4">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const agents = Object.values(agentData);
  const overallHealth = calculateOverallHealth();

  return (
    <div className="space-y-6">
      {/* Header with overall metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">System Health</p>
                <p className="text-2xl font-bold">{overallHealth}%</p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                overallHealth > 80 ? 'bg-green-100' : overallHealth > 60 ? 'bg-yellow-100' : 'bg-red-100'
              }`}>
                <Cpu className={`w-6 h-6 ${
                  overallHealth > 80 ? 'text-green-600' : overallHealth > 60 ? 'text-yellow-600' : 'text-red-600'
                }`} />
              </div>
            </div>
            <Progress value={overallHealth} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Agents</p>
                <p className="text-2xl font-bold">
                  {agents.filter(a => a.status === 'active' || a.status === 'busy').length}
                </p>
              </div>
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Tasks</p>
                <p className="text-2xl font-bold">
                  {agents.reduce((sum, a) => sum + a.performance_metrics.tasks_completed, 0)}
                </p>
              </div>
              <CheckCircle className="w-6 h-6 text-green-600" />
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
            <div className="flex items-center mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Auto' : 'Manual'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Status Grid */}
      <Tabs defaultValue="grid" className="w-full">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="grid">Grid View</TabsTrigger>
            <TabsTrigger value="detailed">Detailed View</TabsTrigger>
          </TabsList>
          <Button onClick={fetchAgentStatus} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        <TabsContent value="grid" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => {
              const trend = getPerformanceTrend(agent.performance_metrics);
              const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Activity;
              
              return (
                <Card 
                  key={agent.agent_name} 
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => setSelectedAgent(agent.agent_name)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{agent.agent_name}</CardTitle>
                      {getStatusBadge(agent.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {agent.current_task && (
                        <div className="text-sm text-gray-600">
                          <strong>Current:</strong> {agent.current_task}
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between text-sm">
                        <span>Success Rate</span>
                        <span className="font-medium">
                          {Math.round(agent.performance_metrics.success_rate * 100)}%
                        </span>
                      </div>
                      
                      <Progress 
                        value={agent.performance_metrics.success_rate * 100} 
                        className="h-2"
                      />
                      
                      <div className="flex items-center justify-between text-sm">
                        <span>Tasks Completed</span>
                        <div className="flex items-center">
                          <span className="font-medium mr-1">
                            {agent.performance_metrics.tasks_completed}
                          </span>
                          <TrendIcon className={`w-4 h-4 ${
                            trend === 'up' ? 'text-green-500' : 
                            trend === 'down' ? 'text-red-500' : 'text-gray-500'
                          }`} />
                        </div>
                      </div>
                      
                      <div className="text-xs text-gray-500">
                        Last active: {formatDistanceToNow(new Date(agent.last_activity), { addSuffix: true })}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="detailed" className="space-y-4">
          <div className="space-y-4">
            {agents.map((agent) => (
              <Card key={agent.agent_name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{agent.agent_name}</CardTitle>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(agent.status)}
                      <Badge variant="secondary">
                        <Zap className="w-3 h-3 mr-1" />
                        {Math.round(agent.performance_metrics.reliability_score * 100)}% Reliable
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Performance Metrics */}
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-700">Performance</h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Success Rate</span>
                            <span>{Math.round(agent.performance_metrics.success_rate * 100)}%</span>
                          </div>
                          <Progress value={agent.performance_metrics.success_rate * 100} />
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Reliability</span>
                            <span>{Math.round(agent.performance_metrics.reliability_score * 100)}%</span>
                          </div>
                          <Progress value={agent.performance_metrics.reliability_score * 100} />
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Avg. Completion Time:</span>
                          <span className="ml-2 font-medium">
                            {Math.round(agent.performance_metrics.avg_completion_time)}s
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Current Status */}
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-700">Current Status</h4>
                      <div className="space-y-2">
                        {agent.current_task && (
                          <div className="text-sm">
                            <span className="text-gray-600">Current Task:</span>
                            <div className="mt-1 p-2 bg-blue-50 rounded text-blue-800">
                              {agent.current_task}
                            </div>
                          </div>
                        )}
                        <div className="text-sm">
                          <span className="text-gray-600">Workload:</span>
                          <span className="ml-2 font-medium">
                            {agent.performance_metrics.current_workload} tasks
                          </span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Last Activity:</span>
                          <span className="ml-2">
                            {formatDistanceToNow(new Date(agent.last_activity), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Queue Status */}
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-700">Queue Status</h4>
                      <div className="space-y-2">
                        {Object.entries(agent.queue_status).map(([key, value]) => (
                          <div key={key} className="flex justify-between text-sm">
                            <span className="text-gray-600 capitalize">
                              {key.replace(/_/g, ' ')}:
                            </span>
                            <span className="font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};