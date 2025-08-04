import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Bell, CheckCircle, AlertCircle, Info } from 'lucide-react';

const SlackNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [newNotification, setNewNotification] = useState({
    channel: '#general',
    message: '',
    agent_name: 'Marketing',
    event_type: 'update',
    priority: 'normal'
  });
  const [integrationStatus, setIntegrationStatus] = useState(null);

  useEffect(() => {
    checkIntegrationStatus();
  }, []);

  const checkIntegrationStatus = async () => {
    try {
      const response = await fetch('/api/integrations/status');
      const data = await response.json();
      const slackStatus = data.integrations.find(i => i.service === 'slack');
      setIntegrationStatus(slackStatus);
    } catch (error) {
      console.error('Failed to check integration status:', error);
    }
  };

  const sendNotification = async () => {
    try {
      const response = await fetch('/api/integrations/slack/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newNotification)
      });

      const data = await response.json();
      if (data.success) {
        setNotifications(prev => [...prev, {
          ...newNotification,
          timestamp: data.timestamp,
          id: Date.now()
        }]);
        setNewNotification(prev => ({ ...prev, message: '' }));
      }
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  };

  const sendCustomMessage = async (channel, text) => {
    try {
      const response = await fetch('/api/integrations/slack/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel, text })
      });

      const data = await response.json();
      if (data.success) {
        setNotifications(prev => [...prev, {
          channel,
          message: text,
          agent_name: 'System',
          event_type: 'custom',
          priority: 'normal',
          timestamp: data.timestamp,
          id: Date.now()
        }]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'high': return <AlertCircle className="w-4 h-4 text-orange-500" />;
      case 'normal': return <Info className="w-4 h-4 text-blue-500" />;
      case 'low': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <Bell className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'normal': return 'bg-blue-100 text-blue-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Integration Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Slack Integration Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {integrationStatus ? (
            <div className="flex items-center gap-2">
              <Badge 
                variant={integrationStatus.status === 'healthy' ? 'default' : 'destructive'}
              >
                {integrationStatus.status}
              </Badge>
              <span className="text-sm text-gray-600">
                Last checked: {new Date(integrationStatus.last_check).toLocaleString()}
              </span>
            </div>
          ) : (
            <p className="text-gray-500">Checking status...</p>
          )}
        </CardContent>
      </Card>

      {/* Send Notification */}
      <Card>
        <CardHeader>
          <CardTitle>Send Slack Notification</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              placeholder="Channel (e.g., #general)"
              value={newNotification.channel}
              onChange={(e) => setNewNotification(prev => ({ ...prev, channel: e.target.value }))}
            />
            <Select
              value={newNotification.agent_name}
              onValueChange={(value) => setNewNotification(prev => ({ ...prev, agent_name: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select Agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Marketing">Marketing</SelectItem>
                <SelectItem value="Finance">Finance</SelectItem>
                <SelectItem value="Legal">Legal</SelectItem>
                <SelectItem value="Manager">Manager</SelectItem>
                <SelectItem value="Cofounder">Cofounder</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              value={newNotification.event_type}
              onValueChange={(value) => setNewNotification(prev => ({ ...prev, event_type: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Event Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="update">Update</SelectItem>
                <SelectItem value="completion">Task Completion</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="approval_needed">Approval Needed</SelectItem>
                <SelectItem value="milestone">Milestone</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={newNotification.priority}
              onValueChange={(value) => setNewNotification(prev => ({ ...prev, priority: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="normal">Normal</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Input
            placeholder="Notification message"
            value={newNotification.message}
            onChange={(e) => setNewNotification(prev => ({ ...prev, message: e.target.value }))}
          />

          <Button 
            onClick={sendNotification}
            disabled={!newNotification.message || !integrationStatus || integrationStatus.status !== 'healthy'}
            className="w-full"
          >
            Send Notification
          </Button>
        </CardContent>
      </Card>

      {/* Recent Notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          {notifications.length === 0 ? (
            <p className="text-gray-500">No notifications sent yet</p>
          ) : (
            <div className="space-y-3">
              {notifications.slice(-10).reverse().map((notification) => (
                <div key={notification.id} className="p-3 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getPriorityIcon(notification.priority)}
                      <div>
                        <p className="text-sm font-medium">
                          {notification.agent_name} - {notification.event_type}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {notification.channel}
                          </Badge>
                          <Badge className={`text-xs ${getPriorityColor(notification.priority)}`}>
                            {notification.priority}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(notification.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button
            variant="outline"
            onClick={() => sendCustomMessage('#general', '🚀 AgentFlow system is running smoothly!')}
            className="w-full"
          >
            Send System Status
          </Button>
          <Button
            variant="outline"
            onClick={() => sendCustomMessage('#agent-updates', '📊 Daily agent performance report is ready')}
            className="w-full"
          >
            Send Performance Update
          </Button>
          <Button
            variant="outline"
            onClick={() => sendCustomMessage('#approvals', '⚠️ New approval request requires attention')}
            className="w-full"
          >
            Send Approval Alert
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default SlackNotifications;