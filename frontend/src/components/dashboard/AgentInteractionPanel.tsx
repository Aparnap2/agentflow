import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  MessageSquare, 
  Users, 
  Settings, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Send,
  Plus,
  RefreshCw,
  Zap,
  StopCircle,
  Play,
  Pause
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

interface CollaborativeDecision {
  decision_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'timeout' | 'failed';
  topic: string;
  agents_involved: string[];
  contributions: Array<{
    agent_name: string;
    perspective: Record<string, any>;
    recommendation?: string;
    confidence: number;
  }>;
  final_decision?: Record<string, any>;
  created_at: string;
  completed_at?: string;
}

interface AgentMeeting {
  meeting_id: string;
  status: 'scheduled' | 'active' | 'completed' | 'cancelled';
  topic: string;
  agents_involved: string[];
  messages: Array<{
    agent_name: string;
    message: string;
    message_type: 'discussion' | 'proposal' | 'question' | 'decision';
    timestamp: string;
  }>;
  decisions_made: Array<Record<string, any>>;
  created_at: string;
  started_at?: string;
  ended_at?: string;
}

interface HumanOverride {
  override_id: string;
  status: 'active' | 'completed' | 'expired' | 'cancelled';
  target_agent: string;
  override_type: 'task_assignment' | 'parameter_change' | 'workflow_modification' | 'emergency_stop';
  instructions: Record<string, any>;
  reason: string;
  created_at: string;
  expires_at?: string;
  completed_at?: string;
}

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  active: 'bg-blue-100 text-blue-800',
  scheduled: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-red-100 text-red-800',
  failed: 'bg-red-100 text-red-800',
  timeout: 'bg-orange-100 text-orange-800',
  expired: 'bg-gray-100 text-gray-800'
};

const overrideTypeIcons = {
  task_assignment: Settings,
  parameter_change: Zap,
  workflow_modification: RefreshCw,
  emergency_stop: StopCircle
};

export const AgentInteractionPanel: React.FC = () => {
  const [decisions, setDecisions] = useState<CollaborativeDecision[]>([]);
  const [meetings, setMeetings] = useState<AgentMeeting[]>([]);
  const [overrides, setOverrides] = useState<HumanOverride[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [newDecisionOpen, setNewDecisionOpen] = useState(false);
  const [newMeetingOpen, setNewMeetingOpen] = useState(false);
  const [newOverrideOpen, setNewOverrideOpen] = useState(false);
  
  // Available agents (would typically come from API)
  const [availableAgents] = useState([
    'Marketing', 'Finance', 'Legal', 'Strategy', 'Cofounder', 'Manager'
  ]);

  // WebSocket connections for real-time updates
  const { data: wsData } = useWebSocket('/api/agent-interaction/ws');

  // Form data
  const [decisionForm, setDecisionForm] = useState({
    topic: '',
    description: '',
    agents_involved: [] as string[],
    priority: 'medium' as 'high' | 'medium' | 'low',
    timeout: 300
  });

  const [meetingForm, setMeetingForm] = useState({
    topic: '',
    agents_involved: [] as string[],
    agenda: [{ item: '', description: '' }],
    duration_minutes: 30,
    priority: 'medium' as 'high' | 'medium' | 'low'
  });

  const [overrideForm, setOverrideForm] = useState({
    target_agent: '',
    override_type: 'task_assignment' as 'task_assignment' | 'parameter_change' | 'workflow_modification' | 'emergency_stop',
    instructions: {},
    reason: '',
    duration_minutes: undefined as number | undefined
  });

  // Fetch data functions
  const fetchDecisions = async () => {
    try {
      // This would fetch from multiple endpoints or a combined endpoint
      // For now, we'll simulate with empty arrays
      setDecisions([]);
    } catch (err) {
      console.error('Error fetching decisions:', err);
    }
  };

  const fetchMeetings = async () => {
    try {
      setMeetings([]);
    } catch (err) {
      console.error('Error fetching meetings:', err);
    }
  };

  const fetchOverrides = async () => {
    try {
      setOverrides([]);
    } catch (err) {
      console.error('Error fetching overrides:', err);
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchDecisions(), fetchMeetings(), fetchOverrides()]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Create functions
  const createDecision = async () => {
    try {
      const response = await fetch('/api/agent-interaction/collaborative-decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: decisionForm.topic,
          description: decisionForm.description,
          agents_involved: decisionForm.agents_involved,
          priority: decisionForm.priority,
          timeout: decisionForm.timeout,
          context: {},
          decision_criteria: {}
        })
      });

      if (!response.ok) throw new Error('Failed to create decision');
      
      setNewDecisionOpen(false);
      setDecisionForm({
        topic: '',
        description: '',
        agents_involved: [],
        priority: 'medium',
        timeout: 300
      });
      await fetchDecisions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create decision');
    }
  };

  const createMeeting = async () => {
    try {
      const response = await fetch('/api/agent-interaction/meeting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: meetingForm.topic,
          agents_involved: meetingForm.agents_involved,
          agenda: meetingForm.agenda,
          duration_minutes: meetingForm.duration_minutes,
          priority: meetingForm.priority
        })
      });

      if (!response.ok) throw new Error('Failed to create meeting');
      
      setNewMeetingOpen(false);
      setMeetingForm({
        topic: '',
        agents_involved: [],
        agenda: [{ item: '', description: '' }],
        duration_minutes: 30,
        priority: 'medium'
      });
      await fetchMeetings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create meeting');
    }
  };

  const createOverride = async () => {
    try {
      const response = await fetch('/api/agent-interaction/human-override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrideForm)
      });

      if (!response.ok) throw new Error('Failed to create override');
      
      setNewOverrideOpen(false);
      setOverrideForm({
        target_agent: '',
        override_type: 'task_assignment',
        instructions: {},
        reason: '',
        duration_minutes: undefined
      });
      await fetchOverrides();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create override');
    }
  };

  // Cancel override
  const cancelOverride = async (overrideId: string) => {
    try {
      const response = await fetch(`/api/agent-interaction/human-override/${overrideId}/cancel`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to cancel override');
      await fetchOverrides();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel override');
    }
  };

  // Initial load
  useEffect(() => {
    fetchAllData();
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (wsData) {
      // Handle real-time updates
      fetchAllData();
    }
  }, [wsData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading interactions...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Agent Interactions</h2>
          <p className="text-gray-600">Manage collaborative decisions, meetings, and overrides</p>
        </div>
        <Button onClick={fetchAllData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Quick Actions */}
      <div className="flex space-x-4">
        <Dialog open={newDecisionOpen} onOpenChange={setNewDecisionOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Decision
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Collaborative Decision</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Topic</label>
                <Input
                  value={decisionForm.topic}
                  onChange={(e) => setDecisionForm({...decisionForm, topic: e.target.value})}
                  placeholder="Decision topic"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Textarea
                  value={decisionForm.description}
                  onChange={(e) => setDecisionForm({...decisionForm, description: e.target.value})}
                  placeholder="Describe the decision needed"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Agents Involved</label>
                <Select
                  value={decisionForm.agents_involved.join(',')}
                  onValueChange={(value) => setDecisionForm({
                    ...decisionForm, 
                    agents_involved: value ? value.split(',') : []
                  })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select agents" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableAgents.map(agent => (
                      <SelectItem key={agent} value={agent}>{agent}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Priority</label>
                <Select
                  value={decisionForm.priority}
                  onValueChange={(value: 'high' | 'medium' | 'low') => 
                    setDecisionForm({...decisionForm, priority: value})
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex space-x-2">
                <Button onClick={createDecision} className="flex-1">Create</Button>
                <Button variant="outline" onClick={() => setNewDecisionOpen(false)}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={newMeetingOpen} onOpenChange={setNewMeetingOpen}>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Users className="w-4 h-4 mr-2" />
              New Meeting
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Schedule Agent Meeting</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Topic</label>
                <Input
                  value={meetingForm.topic}
                  onChange={(e) => setMeetingForm({...meetingForm, topic: e.target.value})}
                  placeholder="Meeting topic"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Duration (minutes)</label>
                <Input
                  type="number"
                  value={meetingForm.duration_minutes}
                  onChange={(e) => setMeetingForm({...meetingForm, duration_minutes: parseInt(e.target.value)})}
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={createMeeting} className="flex-1">Schedule</Button>
                <Button variant="outline" onClick={() => setNewMeetingOpen(false)}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={newOverrideOpen} onOpenChange={setNewOverrideOpen}>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Settings className="w-4 h-4 mr-2" />
              New Override
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Human Override</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Target Agent</label>
                <Select
                  value={overrideForm.target_agent}
                  onValueChange={(value) => setOverrideForm({...overrideForm, target_agent: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select agent" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableAgents.map(agent => (
                      <SelectItem key={agent} value={agent}>{agent}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Override Type</label>
                <Select
                  value={overrideForm.override_type}
                  onValueChange={(value: any) => setOverrideForm({...overrideForm, override_type: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="task_assignment">Task Assignment</SelectItem>
                    <SelectItem value="parameter_change">Parameter Change</SelectItem>
                    <SelectItem value="workflow_modification">Workflow Modification</SelectItem>
                    <SelectItem value="emergency_stop">Emergency Stop</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Reason</label>
                <Textarea
                  value={overrideForm.reason}
                  onChange={(e) => setOverrideForm({...overrideForm, reason: e.target.value})}
                  placeholder="Reason for override"
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={createOverride} className="flex-1">Create</Button>
                <Button variant="outline" onClick={() => setNewOverrideOpen(false)}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="decisions" className="w-full">
        <TabsList>
          <TabsTrigger value="decisions">
            Decisions ({decisions.length})
          </TabsTrigger>
          <TabsTrigger value="meetings">
            Meetings ({meetings.length})
          </TabsTrigger>
          <TabsTrigger value="overrides">
            Overrides ({overrides.filter(o => o.status === 'active').length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="decisions" className="space-y-4">
          {decisions.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4" />
                  <p>No collaborative decisions</p>
                  <p className="text-sm">Create a new decision to get started</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            decisions.map((decision) => (
              <Card key={decision.decision_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{decision.topic}</CardTitle>
                    <Badge className={statusColors[decision.status]}>
                      {decision.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        <span>Agents: {decision.agents_involved.join(', ')}</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        <span>Created: {formatDistanceToNow(new Date(decision.created_at), { addSuffix: true })}</span>
                      </div>
                    </div>
                    
                    {decision.contributions.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Contributions ({decision.contributions.length})</h4>
                        <div className="space-y-2">
                          {decision.contributions.map((contribution, index) => (
                            <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                              <div className="font-medium">{contribution.agent_name}</div>
                              {contribution.recommendation && (
                                <div className="text-gray-600">{contribution.recommendation}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {decision.final_decision && (
                      <div className="p-3 bg-green-50 rounded">
                        <h4 className="font-semibold text-green-800 mb-1">Final Decision</h4>
                        <p className="text-sm text-green-700">{decision.final_decision.summary}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="meetings" className="space-y-4">
          {meetings.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4" />
                  <p>No agent meetings</p>
                  <p className="text-sm">Schedule a meeting to facilitate collaboration</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            meetings.map((meeting) => (
              <Card key={meeting.meeting_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{meeting.topic}</CardTitle>
                    <Badge className={statusColors[meeting.status]}>
                      {meeting.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Participants: {meeting.agents_involved.join(', ')}</span>
                      <span>Created: {formatDistanceToNow(new Date(meeting.created_at), { addSuffix: true })}</span>
                    </div>
                    
                    {meeting.messages.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Recent Messages ({meeting.messages.length})</h4>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {meeting.messages.slice(-3).map((message, index) => (
                            <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                              <div className="font-medium">{message.agent_name}</div>
                              <div className="text-gray-600">{message.message}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="overrides" className="space-y-4">
          {overrides.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Settings className="w-12 h-12 mx-auto mb-4" />
                  <p>No active overrides</p>
                  <p className="text-sm">All agents are operating normally</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            overrides.map((override) => {
              const OverrideIcon = overrideTypeIcons[override.override_type];
              return (
                <Card key={override.override_id} className={`border-l-4 ${
                  override.status === 'active' ? 'border-l-red-500' : 'border-l-gray-300'
                }`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <OverrideIcon className="w-5 h-5" />
                        <CardTitle className="text-lg">{override.target_agent}</CardTitle>
                      </div>
                      <Badge className={statusColors[override.status]}>
                        {override.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm font-medium">Type: </span>
                        <span className="text-sm capitalize">{override.override_type.replace(/_/g, ' ')}</span>
                      </div>
                      <div>
                        <span className="text-sm font-medium">Reason: </span>
                        <span className="text-sm">{override.reason}</span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Created: {formatDistanceToNow(new Date(override.created_at), { addSuffix: true })}</span>
                        {override.expires_at && (
                          <span>Expires: {formatDistanceToNow(new Date(override.expires_at), { addSuffix: true })}</span>
                        )}
                      </div>
                      
                      {override.status === 'active' && (
                        <div className="flex space-x-2">
                          <Button
                            onClick={() => cancelOverride(override.override_id)}
                            size="sm"
                            variant="destructive"
                          >
                            Cancel Override
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};