import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Bell, 
  MessageSquare, 
  Users,
  RefreshCw,
  X,
  ArrowRight
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  source_agent: string;
  created_at: string;
  read: boolean;
}

interface SearchResult {
  id: string;
  type: 'conversation' | 'task' | 'document' | 'decision';
  title: string;
  content: string;
  agent: string;
  created_at: string;
  relevance: number;
}

interface AgentConversation {
  agent_name: string;
  last_message: string;
  last_activity: string;
  unread_count: number;
}

export const UnifiedUserExperience: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [conversations, setConversations] = useState<AgentConversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);

  // WebSocket connection for real-time updates
  const { data: wsData } = useWebSocket('/api/notifications/ws');

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      // In a real implementation, this would fetch from an API
      // For now, we'll use mock data
      const mockNotifications: Notification[] = [
        {
          id: '1',
          type: 'warning',
          title: 'Priority Conflict',
          message: 'Marketing and Finance agents have conflicting priorities for budget allocation',
          source_agent: 'Manager',
          created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
          read: false
        },
        {
          id: '2',
          type: 'info',
          title: 'Task Completed',
          message: 'Content calendar for Q3 has been completed',
          source_agent: 'Marketing',
          created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
          read: true
        },
        {
          id: '3',
          type: 'success',
          title: 'Decision Approved',
          message: 'Budget allocation for Q3 marketing campaigns approved',
          source_agent: 'Finance',
          created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
          read: false
        }
      ];
      
      setNotifications(mockNotifications);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch agent conversations
  const fetchConversations = async () => {
    try {
      // In a real implementation, this would fetch from an API
      // For now, we'll use mock data
      const mockConversations: AgentConversation[] = [
        {
          agent_name: 'Marketing',
          last_message: 'I've completed the content calendar for Q3',
          last_activity: new Date(Date.now() - 1000 * 60 * 10).toISOString(), // 10 minutes ago
          unread_count: 0
        },
        {
          agent_name: 'Finance',
          last_message: 'Budget allocation for Q3 has been approved',
          last_activity: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
          unread_count: 2
        },
        {
          agent_name: 'Legal',
          last_message: 'I've reviewed the terms of service update',
          last_activity: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
          unread_count: 1
        },
        {
          agent_name: 'Strategy',
          last_message: 'Q4 planning is now complete',
          last_activity: new Date(Date.now() - 1000 * 60 * 60).toISOString(), // 1 hour ago
          unread_count: 0
        }
      ];
      
      setConversations(mockConversations);
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };

  // Search across agents
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      // In a real implementation, this would search via an API
      // For now, we'll use mock results
      setTimeout(() => {
        const mockResults: SearchResult[] = [
          {
            id: '1',
            type: 'conversation',
            title: 'Marketing Campaign Discussion',
            content: `...${searchQuery}...`,
            agent: 'Marketing',
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
            relevance: 0.95
          },
          {
            id: '2',
            type: 'task',
            title: 'Budget Review',
            content: `...${searchQuery}...`,
            agent: 'Finance',
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
            relevance: 0.85
          },
          {
            id: '3',
            type: 'document',
            title: 'Q3 Strategy Document',
            content: `...${searchQuery}...`,
            agent: 'Strategy',
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(), // 3 days ago
            relevance: 0.75
          }
        ];
        
        setSearchResults(mockResults);
        setIsSearching(false);
      }, 500);
    } catch (err) {
      console.error('Error searching:', err);
      setIsSearching(false);
    }
  };

  // Mark notification as read
  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  // Initial load
  useEffect(() => {
    fetchNotifications();
    fetchConversations();
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (wsData && wsData.type === 'notification') {
      // In a real implementation, this would handle new notifications
      fetchNotifications();
    }
  }, [wsData]);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="space-y-6">
      {/* Header with Search and Notifications */}
      <div className="flex items-center justify-between">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
          <Input
            placeholder="Search across all agents..."
            className="pl-8 pr-4"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          {isSearching && <RefreshCw className="absolute right-2 top-2.5 h-4 w-4 animate-spin" />}
        </div>
        
        <div className="relative">
          <Button 
            variant="outline" 
            className="relative"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </Button>
          
          {showNotifications && (
            <Card className="absolute right-0 mt-2 w-80 z-50">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Notifications</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setShowNotifications(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="text-center text-gray-500 py-4">
                    <p>No notifications</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {notifications.map((notification) => (
                      <div 
                        key={notification.id} 
                        className={`p-2 rounded-md ${notification.read ? 'bg-gray-50' : 'bg-blue-50'}`}
                        onClick={() => markAsRead(notification.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="font-medium text-sm">{notification.title}</div>
                          <Badge variant={notification.read ? 'outline' : 'default'} className="text-[10px]">
                            {notification.source_agent}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Search Results for "{searchQuery}"</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSearchResults([])}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {searchResults.map((result) => (
                <div key={result.id} className="p-2 hover:bg-gray-50 rounded-md cursor-pointer">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium">{result.title}</div>
                      <p className="text-sm text-gray-600">{result.content}</p>
                    </div>
                    <Badge variant="outline">{result.agent}</Badge>
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                    <span>{result.type}</span>
                    <span>{formatDistanceToNow(new Date(result.created_at), { addSuffix: true })}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contextual Switching Between Agent Conversations */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Conversations</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue={activeConversation || conversations[0]?.agent_name}>
            <TabsList className="grid grid-cols-4">
              {conversations.map((conversation) => (
                <TabsTrigger 
                  key={conversation.agent_name} 
                  value={conversation.agent_name}
                  className="relative"
                  onClick={() => setActiveConversation(conversation.agent_name)}
                >
                  {conversation.agent_name}
                  {conversation.unread_count > 0 && (
                    <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center">
                      {conversation.unread_count}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
            
            {conversations.map((conversation) => (
              <TabsContent key={conversation.agent_name} value={conversation.agent_name}>
                <div className="p-4 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-2 mb-4">
                    <Users className="h-5 w-5" />
                    <h3 className="font-medium">{conversation.agent_name} Agent</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-start space-x-2">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        {conversation.agent_name.charAt(0)}
                      </div>
                      <div className="bg-blue-50 p-3 rounded-lg rounded-tl-none flex-1">
                        <p className="text-sm">{conversation.last_message}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDistanceToNow(new Date(conversation.last_activity), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center">
                      <Input 
                        placeholder={`Message ${conversation.agent_name} agent...`}
                        className="flex-1 mr-2"
                      />
                      <Button size="sm">
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};