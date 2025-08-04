import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Coffee,
  FileText,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Users,
  Zap,
  Calendar,
  Target,
  AlertCircle,
  ArrowRight
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

interface AgentActivity {
  agent_name: string;
  tasks_completed: number;
  tasks_failed: number;
  key_achievements: string[];
  issues_encountered: string[];
  time_active: number;
}

interface PriorityAlert {
  id: string;
  type: 'conflict' | 'deadline' | 'resource_shortage' | 'error';
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  agents_involved: string[];
  created_at: string;
  requires_attention: boolean;
}

interface CrossFunctionalDependency {
  id: string;
  source_agent: string;
  target_agent: string;
  dependency_type: 'data' | 'approval' | 'resource' | 'coordination';
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  created_at: string;
  deadline?: string;
}

interface DecisionItem {
  id: string;
  title: string;
  description: string;
  decision_type: 'strategic' | 'operational' | 'resource_allocation' | 'conflict_resolution';
  agents_involved: string[];
  options: Array<{ option: string; description: string }>;
  recommendation?: { option: string; reasoning: string };
  priority: 'high' | 'medium' | 'low';
  deadline?: string;
  created_at: string;
  context: Record<string, any>;
}

interface MorningBriefData {
  date: string;
  time_period: { start: string; end: string };
  summary: Record<string, any>;
  agent_activities: AgentActivity[];
  priority_alerts: PriorityAlert[];
  cross_functional_dependencies: CrossFunctionalDependency[];
  decision_queue: DecisionItem[];
  recommendations: string[];
  generated_at: string;
}

const alertTypeIcons = {
  conflict: AlertTriangle,
  deadline: Clock,
  resource_shortage: Zap,
  error: AlertCircle
};

const alertSeverityColors = {
  high: 'bg-red-100 border-red-300 text-red-800',
  medium: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  low: 'bg-blue-100 border-blue-300 text-blue-800'
};

const dependencyStatusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  blocked: 'bg-red-100 text-red-800'
};

const decisionPriorityColors = {
  high: 'border-l-red-500',
  medium: 'border-l-yellow-500',
  low: 'border-l-blue-500'
};

export const MorningBrief: React.FC = () => {
  const [briefData, setBriefData] = useState<MorningBriefData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<string | null>(null);

  // Fetch morning brief data
  const fetchMorningBrief = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/morning-brief/today');
      if (!response.ok) throw new Error('Failed to fetch morning brief');
      
      const data = await response.json();
      setBriefData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Resolve decision
  const resolveDecision = async (decisionId: string, resolution: Record<string, any>) => {
    try {
      const response = await fetch(`/api/morning-brief/decision-queue/${decisionId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resolution)
      });
      
      if (!response.ok) throw new Error('Failed to resolve decision');
      
      // Refresh data
      await fetchMorningBrief();
      setSelectedDecision(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve decision');
    }
  };

  // Initial load
  useEffect(() => {
    fetchMorningBrief();
  }, []);

  if (loading && !briefData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Coffee className="w-8 h-8 animate-pulse text-amber-600" />
        <span className="ml-2">Preparing your morning brief...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Error loading morning brief: {error}
          <Button onClick={fetchMorningBrief} className="ml-4" size="sm">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!briefData) return null;

  const highPriorityAlerts = briefData.priority_alerts.filter(a => a.severity === 'high');
  const urgentDecisions = briefData.decision_queue.filter(d => d.priority === 'high');
  const blockedDependencies = briefData.cross_functional_dependencies.filter(d => d.status === 'blocked');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Coffee className="w-8 h-8 text-amber-600" />
          <div>
            <h1 className="text-2xl font-bold">Good Morning!</h1>
            <p className="text-gray-600">
              Brief for {format(new Date(briefData.date), 'EEEE, MMMM do, yyyy')}
            </p>
          </div>
        </div>
        <Button onClick={fetchMorningBrief} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Executive Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Agents</p>
                <p className="text-2xl font-bold">{briefData.summary.active_agents || 0}</p>
                <p className="text-xs text-gray-500">
                  of {briefData.summary.total_agents || 0} total
                </p>
              </div>
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasks Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {briefData.summary.total_tasks_completed || 0}
                </p>
                <p className="text-xs text-gray-500">overnight</p>
              </div>
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Priority Alerts</p>
                <p className={`text-2xl font-bold ${highPriorityAlerts.length > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                  {highPriorityAlerts.length}
                </p>
                <p className="text-xs text-gray-500">require attention</p>
              </div>
              <AlertTriangle className={`w-6 h-6 ${highPriorityAlerts.length > 0 ? 'text-red-600' : 'text-gray-400'}`} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Decisions</p>
                <p className={`text-2xl font-bold ${urgentDecisions.length > 0 ? 'text-amber-600' : 'text-gray-400'}`}>
                  {urgentDecisions.length}
                </p>
                <p className="text-xs text-gray-500">high priority</p>
              </div>
              <Target className={`w-6 h-6 ${urgentDecisions.length > 0 ? 'text-amber-600' : 'text-gray-400'}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Critical Alerts */}
      {highPriorityAlerts.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>{highPriorityAlerts.length} high-priority alerts</strong> require immediate attention.
            Review the alerts tab for details.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agent Activity</TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts ({briefData.priority_alerts.length})
          </TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="decisions">
            Decisions ({urgentDecisions.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Key Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {briefData.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                    <ArrowRight className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-blue-800">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Time Period Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calendar className="w-5 h-5 mr-2" />
                Activity Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Time Period</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">From:</span>
                      <span>{format(new Date(briefData.time_period.start), 'MMM d, h:mm a')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">To:</span>
                      <span>{format(new Date(briefData.time_period.end), 'MMM d, h:mm a')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Duration:</span>
                      <span>
                        {formatDistanceToNow(
                          new Date(new Date(briefData.time_period.end).getTime() - new Date(briefData.time_period.start).getTime())
                        )}
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-3">Key Metrics</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tasks Completed:</span>
                      <span className="font-medium text-green-600">
                        {briefData.summary.total_tasks_completed || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Issues Encountered:</span>
                      <span className="font-medium text-red-600">
                        {briefData.summary.total_issues || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Active Agents:</span>
                      <span className="font-medium">
                        {briefData.summary.active_agents || 0}/{briefData.summary.total_agents || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {briefData.agent_activities.map((activity) => (
              <Card key={activity.agent_name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{activity.agent_name}</CardTitle>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">
                        {activity.tasks_completed} completed
                      </Badge>
                      {activity.tasks_failed > 0 && (
                        <Badge variant="destructive">
                          {activity.tasks_failed} failed
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <h4 className="font-semibold text-green-700 mb-2">Key Achievements</h4>
                      {activity.key_achievements.length > 0 ? (
                        <ul className="space-y-1 text-sm">
                          {activity.key_achievements.map((achievement, index) => (
                            <li key={index} className="flex items-start">
                              <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                              <span>{achievement}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-gray-500">No achievements recorded</p>
                      )}
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-red-700 mb-2">Issues Encountered</h4>
                      {activity.issues_encountered.length > 0 ? (
                        <ul className="space-y-1 text-sm">
                          {activity.issues_encountered.map((issue, index) => (
                            <li key={index} className="flex items-start">
                              <AlertCircle className="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                              <span>{issue}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-gray-500">No issues reported</p>
                      )}
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-2">Activity Metrics</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Time Active:</span>
                          <span>{activity.time_active.toFixed(1)}h</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Success Rate:</span>
                          <span>
                            {activity.tasks_completed + activity.tasks_failed > 0 
                              ? Math.round((activity.tasks_completed / (activity.tasks_completed + activity.tasks_failed)) * 100)
                              : 0
                            }%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          {briefData.priority_alerts.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                  <p>No priority alerts</p>
                  <p className="text-sm">All systems operating normally</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            briefData.priority_alerts.map((alert) => {
              const AlertIcon = alertTypeIcons[alert.type];
              return (
                <Card key={alert.id} className={`border-l-4 ${
                  alert.severity === 'high' ? 'border-l-red-500' : 
                  alert.severity === 'medium' ? 'border-l-yellow-500' : 'border-l-blue-500'
                }`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertIcon className="w-5 h-5" />
                        <CardTitle className="text-lg">{alert.title}</CardTitle>
                      </div>
                      <Badge className={alertSeverityColors[alert.severity]}>
                        {alert.severity} priority
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <p className="text-gray-700">{alert.description}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-1" />
                          <span>Agents: {alert.agents_involved.join(', ')}</span>
                        </div>
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>Created: {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}</span>
                        </div>
                      </div>
                      {alert.requires_attention && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            This alert requires immediate attention and manual intervention.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </TabsContent>

        <TabsContent value="dependencies" className="space-y-4">
          {briefData.cross_functional_dependencies.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Zap className="w-12 h-12 mx-auto mb-4 text-green-500" />
                  <p>No cross-functional dependencies</p>
                  <p className="text-sm">All agents are working independently</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            briefData.cross_functional_dependencies.map((dependency) => (
              <Card key={dependency.id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{dependency.source_agent}</span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{dependency.target_agent}</span>
                    </div>
                    <Badge className={dependencyStatusColors[dependency.status]}>
                      {dependency.status}
                    </Badge>
                  </div>
                  <p className="text-gray-700 mb-2">{dependency.description}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Type: {dependency.dependency_type}</span>
                    <span>Created: {formatDistanceToNow(new Date(dependency.created_at), { addSuffix: true })}</span>
                    {dependency.deadline && (
                      <span>Deadline: {format(new Date(dependency.deadline), 'MMM d, h:mm a')}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="decisions" className="space-y-4">
          {briefData.decision_queue.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Target className="w-12 h-12 mx-auto mb-4 text-green-500" />
                  <p>No pending decisions</p>
                  <p className="text-sm">All decisions have been resolved</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            briefData.decision_queue.map((decision) => (
              <Card key={decision.id} className={`border-l-4 ${decisionPriorityColors[decision.priority]}`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{decision.title}</CardTitle>
                    <Badge variant={decision.priority === 'high' ? 'destructive' : 'secondary'}>
                      {decision.priority} priority
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-gray-700">{decision.description}</p>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        <span>Agents: {decision.agents_involved.join(', ')}</span>
                      </div>
                      <span>Type: {decision.decision_type}</span>
                      {decision.deadline && (
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>Deadline: {format(new Date(decision.deadline), 'MMM d, h:mm a')}</span>
                        </div>
                      )}
                    </div>

                    {decision.options.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Options:</h4>
                        <div className="space-y-2">
                          {decision.options.map((option, index) => (
                            <div key={index} className="p-2 bg-gray-50 rounded">
                              <div className="font-medium">{option.option}</div>
                              <div className="text-sm text-gray-600">{option.description}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {decision.recommendation && (
                      <div className="p-3 bg-blue-50 rounded">
                        <h4 className="font-semibold text-blue-800 mb-1">Recommendation:</h4>
                        <p className="text-sm text-blue-700">{decision.recommendation.reasoning}</p>
                      </div>
                    )}

                    <div className="flex space-x-2">
                      <Button
                        onClick={() => resolveDecision(decision.id, { 
                          resolution: decision.recommendation?.option || 'approved',
                          resolved_by: 'human'
                        })}
                        size="sm"
                      >
                        Approve Recommendation
                      </Button>
                      <Button
                        onClick={() => setSelectedDecision(decision.id)}
                        size="sm"
                        variant="outline"
                      >
                        Custom Resolution
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};