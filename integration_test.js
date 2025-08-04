// Integration test for AgentFlow
// Run with: node integration_test.js

const axios = require('axios');
const WebSocket = require('ws');
const chalk = require('chalk');

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws/agent-updates';
const TEST_TIMEOUT = 30000; // 30 seconds

// Test results
let passedTests = 0;
let failedTests = 0;

// Helper functions
const log = {
  info: (msg) => console.log(chalk.blue(`ℹ️ ${msg}`)),
  success: (msg) => console.log(chalk.green(`✅ ${msg}`)),
  error: (msg) => console.log(chalk.red(`❌ ${msg}`)),
  warning: (msg) => console.log(chalk.yellow(`⚠️ ${msg}`))
};

const testApi = async (endpoint, method = 'get', data = null) => {
  try {
    const config = {
      method,
      url: `${API_BASE_URL}${endpoint}`,
      ...(data && { data })
    };
    
    const response = await axios(config);
    return response.data;
  } catch (error) {
    throw new Error(`API Error: ${error.message}`);
  }
};

const runTest = async (name, testFn) => {
  log.info(`Running test: ${name}`);
  try {
    await testFn();
    log.success(`Test passed: ${name}`);
    passedTests++;
  } catch (error) {
    log.error(`Test failed: ${name}`);
    log.error(`  ${error.message}`);
    failedTests++;
  }
};

// Tests
const tests = [
  // Test 1: Health check
  async () => {
    const health = await testApi('/health');
    if (health.status !== 'healthy') {
      throw new Error('Health check failed');
    }
  },
  
  // Test 2: Agent status
  async () => {
    const agents = await testApi('/agents/status');
    if (!agents || Object.keys(agents).length === 0) {
      throw new Error('No agents found');
    }
    
    // Check for required agents
    const requiredAgents = ['Cofounder', 'Manager', 'Product', 'Finance', 'Marketing', 'Legal'];
    for (const agent of requiredAgents) {
      if (!agents[agent]) {
        throw new Error(`Required agent not found: ${agent}`);
      }
    }
  },
  
  // Test 3: Start conversation
  async () => {
    const conversation = await testApi('/conversation/start', 'post', {
      message: 'Test startup idea for integration testing'
    });
    
    if (!conversation.conversation_id) {
      throw new Error('No conversation ID returned');
    }
    
    if (!conversation.response) {
      throw new Error('No response returned');
    }
    
    // Store conversation ID for later tests
    global.conversationId = conversation.conversation_id;
  },
  
  // Test 4: Continue conversation
  async () => {
    if (!global.conversationId) {
      throw new Error('No conversation ID available');
    }
    
    const response = await testApi(`/conversation/${global.conversationId}/message`, 'post', {
      message: 'This is a follow-up message for testing'
    });
    
    if (!response.response) {
      throw new Error('No response returned');
    }
  },
  
  // Test 5: WebSocket connection
  async () => {
    return new Promise((resolve, reject) => {
      try {
        const ws = new WebSocket(WS_URL);
        
        ws.on('open', () => {
          log.info('WebSocket connected');
        });
        
        ws.on('message', (data) => {
          try {
            const message = JSON.parse(data);
            log.info(`WebSocket message received: ${message.type}`);
            ws.close();
            resolve();
          } catch (error) {
            reject(new Error(`Failed to parse WebSocket message: ${error.message}`));
          }
        });
        
        ws.on('error', (error) => {
          reject(new Error(`WebSocket error: ${error.message}`));
        });
        
        // Timeout for WebSocket test
        setTimeout(() => {
          ws.close();
          reject(new Error('WebSocket test timed out'));
        }, 5000);
      } catch (error) {
        reject(new Error(`WebSocket connection failed: ${error.message}`));
      }
    });
  },
  
  // Test 6: Get outputs
  async () => {
    const outputs = await testApi('/outputs');
    if (typeof outputs !== 'object') {
      throw new Error('Invalid outputs response');
    }
  },
  
  // Test 7: Generate report
  async () => {
    const report = await testApi('/reports/comprehensive');
    if (!report || !report.report_type) {
      throw new Error('Invalid report response');
    }
  }
];

// Run all tests
const runAllTests = async () => {
  log.info('Starting integration tests...');
  
  for (let i = 0; i < tests.length; i++) {
    await runTest(`Test ${i + 1}`, tests[i]);
  }
  
  log.info('Integration tests completed');
  log.success(`Passed: ${passedTests}`);
  if (failedTests > 0) {
    log.error(`Failed: ${failedTests}`);
    process.exit(1);
  } else {
    log.success('All tests passed!');
    process.exit(0);
  }
};

// Set timeout for all tests
setTimeout(() => {
  log.error('Tests timed out');
  process.exit(1);
}, TEST_TIMEOUT);

// Run tests
runAllTests().catch((error) => {
  log.error(`Test runner error: ${error.message}`);
  process.exit(1);
});