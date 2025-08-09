import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  BarChart3, 
  Coffee, 
  GitBranch, 
  MessageSquare, 
  Settings, 
  Users,
  Zap,
  Bell,
  Calendar,
  TrendingUp,
  Search,
  Shield
} from 'lucide-react';

import { AgentStatusDashboard } from './AgentStatusDashboard';
import { TaskFlowVisualization } from './TaskFlowVisualization';
import { MorningBrief } from './MorningBrief';
import { AgentInteractionPanel } from './AgentInteractionPanel';
import { UnifiedUserExperience } from './UnifiedUserExperience';
import PRDCompliancePanel from '../PRD/PRDCompliancePanel';

interface DashboardStats {
  totalAgents: number;
  activeAgents: number;
  tasksCompleted: number;
  activeConflicts: number;
  pendingDecisions: number;
  systemHealth: number;
}

export const MainDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Real stats from API
  const [stats, setStats] = useState<DashboardStats>({
    totalAgents: 0,
    activeAgents: 0,
    tasksCompleted: 0,
    activeConflicts: 0,
    pendingDecisions: 0,
    systemHealth: 0
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // Fetch real stats from API endpoints
      const response = await fetch('/api/health', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const healthData = await response.json();
      
      setStats({
        totalAgents: healthData.agents_available || 0,
        activeAgents: healthData.agents_available || 0,
        tasksCompleted: 0, // Would come from analytics API
        activeConflicts: 0, // Would come from workflow API
        pendingDecisions: 0, // Would come from approvals API
        systemHealth: healthData.status === 'healthy' ? 95 : 50
      });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  };

  const getHealthColor = (health: number) => {
    if (health >= 80) return 'text-green-600';
    if (health >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthBadgeColor = (health: number) => {
    if (health >= 80) return 'bg-green-100 text-green-800';
    if (health >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Zap className="w-8 h-8 text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">AgentFlow</h1>
              </div>
              <Badge variant="outline" className="text-xs">
                Multi-Agent Dashboard
              </Badge>
            </div>
            
            <div className="flex items-center space-x-4">
              <Badge className={getHealthBadgeColor(stats.systemHealth)}>
                System Health: {stats.systemHealth}%
              </Badge>
              <Button variant="outline" size="sm">
                <Bell className="w-4 h-4 mr-2" />
                Notifications
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => window.location.href = '?view=classic'}
              >
                Switch to Classic View
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Agent Status</span>
            </TabsTrigger>
            <TabsTrigger value="flow" className="flex items-center space-x-2">
              <GitBranch className="w-4 h-4" />
              <span>Task Flow</span>
            </TabsTrigger>
            <TabsTrigger value="brief" className="flex items-center space-x-2">
              <Coffee className="w-4 h-4" />
              <span>Morning Brief</span>
            </TabsTrigger>
            <TabsTrigger value="interactions" className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4" />
              <span>Interactions</span>
            </TabsTrigger>
            <TabsTrigger value="prd" className="flex items-center space-x-2">
              <Shield className="w-4 h-4" />
              <span>PRD Compliance</span>
            </TabsTrigger>
            <TabsTrigger value="unified" className="flex items-center space-x-2">
              <Search className="w-4 h-4" />
              <span>Unified Experience</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Overview Dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalAgents}</div>
                  <p className="text-xs text-muted-foreground">
                    {stats.activeAgents} currently active
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.tasksCompleted}</div>
                  <p className="text-xs text-muted-foreground">
                    +12% from yesterday
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Conflicts</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${stats.activeConflicts > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {stats.activeConflicts}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {stats.activeConflicts > 0 ? 'Require attention' : 'All resolved'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">System Health</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getHealthColor(stats.systemHealth)}`}>
                    {stats.systemHealth}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    All systems operational
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                    onClick={() => setActiveTab('brief')}
                  >
                    <Coffee className="w-6 h-6" />
                    <span>View Morning Brief</span>
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                    onClick={() => setActiveTab('flow')}
                  >
                    <GitBranch className="w-6 h-6" />
                    <span>Monitor Task Flow</span>
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                    onClick={() => setActiveTab('interactions')}
                  >
                    <MessageSquare className="w-6 h-6" />
                    <span>Manage Interactions</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 p-3 bg-green-50 rounded-lg">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Marketing Agent completed content strategy task</p>
                      <p className="text-xs text-gray-500">2 minutes ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 p-3 bg-blue-50 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Finance Agent requested budget approval from Manager</p>
                      <p className="text-xs text-gray-500">5 minutes ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 p-3 bg-yellow-50 rounded-lg">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Priority conflict detected between Legal and Strategy agents</p>
                      <p className="text-xs text-gray-500">8 minutes ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 p-3 bg-green-50 rounded-lg">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Collaborative decision finalized for Q4 planning</p>
                      <p className="text-xs text-gray-500">15 minutes ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agents">
            <AgentStatusDashboard />
          </TabsContent>

          <TabsContent value="flow">
            <TaskFlowVisualization />
          </TabsContent>

          <TabsContent value="brief">
            <MorningBrief />
          </TabsContent>

          <TabsContent value="interactions">
            <AgentInteractionPanel />
          </TabsContent>

          <TabsContent value="prd">
            <PRDCompliancePanel />
          </TabsContent>

          <TabsContent value="unified">
            <UnifiedUserExperience />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};