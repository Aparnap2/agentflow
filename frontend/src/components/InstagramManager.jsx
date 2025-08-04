import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';

const InstagramManager = () => {
  const [posts, setPosts] = useState([]);
  const [dms, setDms] = useState([]);
  const [newPost, setNewPost] = useState({
    content: '',
    hashtags: '',
    media_urls: []
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDMs();
  }, []);

  const fetchDMs = async () => {
    try {
      const response = await fetch('/api/integrations/instagram/dms');
      const data = await response.json();
      if (data.success) {
        setDms(data.conversations);
      }
    } catch (error) {
      console.error('Failed to fetch DMs:', error);
    }
  };

  const createPost = async () => {
    setLoading(true);
    try {
      const hashtags = newPost.hashtags.split(',').map(tag => tag.trim()).filter(Boolean);
      
      const response = await fetch('/api/integrations/instagram/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newPost.content,
          hashtags: hashtags,
          media_urls: newPost.media_urls
        })
      });

      const data = await response.json();
      if (data.success) {
        setPosts(prev => [...prev, data]);
        setNewPost({ content: '', hashtags: '', media_urls: [] });
      }
    } catch (error) {
      console.error('Failed to create post:', error);
    } finally {
      setLoading(false);
    }
  };

  const respondToDM = async (conversationId, message) => {
    try {
      const response = await fetch('/api/integrations/instagram/dm/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: message
        })
      });

      if (response.ok) {
        fetchDMs(); // Refresh DMs
      }
    } catch (error) {
      console.error('Failed to respond to DM:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Create Post Section */}
      <Card>
        <CardHeader>
          <CardTitle>Create Instagram Post</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="What's happening?"
            value={newPost.content}
            onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
            rows={3}
          />
          <Input
            placeholder="Hashtags (comma separated)"
            value={newPost.hashtags}
            onChange={(e) => setNewPost(prev => ({ ...prev, hashtags: e.target.value }))}
          />
          <Button 
            onClick={createPost} 
            disabled={loading || !newPost.content}
            className="w-full"
          >
            {loading ? 'Posting...' : 'Create Post'}
          </Button>
        </CardContent>
      </Card>

      {/* Recent Posts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Posts</CardTitle>
        </CardHeader>
        <CardContent>
          {posts.length === 0 ? (
            <p className="text-gray-500">No posts yet</p>
          ) : (
            <div className="space-y-3">
              {posts.map((post, index) => (
                <div key={index} className="p-3 border rounded-lg">
                  <p className="text-sm">{post.content || 'Post created'}</p>
                  <div className="flex justify-between items-center mt-2">
                    <Badge variant="outline">
                      {post.status}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {new Date(post.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* DM Management */}
      <Card>
        <CardHeader>
          <CardTitle>Instagram DMs</CardTitle>
        </CardHeader>
        <CardContent>
          {dms.length === 0 ? (
            <p className="text-gray-500">No DM conversations</p>
          ) : (
            <div className="space-y-3">
              {dms.map((dm, index) => (
                <div key={index} className="p-3 border rounded-lg">
                  <p className="text-sm">{dm.message}</p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs text-gray-500">
                      From: {dm.sender_id}
                    </span>
                    <Button
                      size="sm"
                      onClick={() => respondToDM(dm.conversation_id, "Thanks for your message! We'll get back to you soon.")}
                    >
                      Auto Reply
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InstagramManager;