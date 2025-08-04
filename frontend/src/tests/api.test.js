// Simple API integration test

import api from '../lib/api';

// Mock fetch for testing
global.fetch = jest.fn(() => 
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ status: 'healthy' }),
  })
);

describe('API Client', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('health check returns status', async () => {
    const response = await api.get('/health');
    expect(response.data).toEqual({ status: 'healthy' });
  });

  test('startConversation sends correct data', async () => {
    const message = 'Test message';
    await api.startConversation(message);
    
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/conversation/start',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ message }),
      })
    );
  });

  test('sendMessage sends correct data', async () => {
    const conversationId = 'test-id';
    const message = 'Test message';
    await api.sendMessage(conversationId, message);
    
    expect(fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/conversation/${conversationId}/message`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ message }),
      })
    );
  });

  test('approveConversation sends correct request', async () => {
    const conversationId = 'test-id';
    await api.approveConversation(conversationId);
    
    expect(fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/conversation/${conversationId}/approve`,
      expect.objectContaining({
        method: 'POST',
      })
    );
  });
});