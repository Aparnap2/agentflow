// Simple backend connection test
// Run with: node test_backend_connection.js

const http = require('http');

console.log('🧪 Testing backend connection...');

// Test the health endpoint
const req = http.get('http://localhost:8000/api/health', (res) => {
  console.log(`🔍 Status Code: ${res.statusCode}`);
  
  if (res.statusCode !== 200) {
    console.error('❌ Backend connection failed!');
    process.exit(1);
  }
  
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    try {
      const response = JSON.parse(data);
      console.log('📊 Response:', response);
      
      if (response.status === 'healthy') {
        console.log('✅ Backend connection successful!');
        process.exit(0);
      } else {
        console.error('❌ Backend is not healthy!');
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ Failed to parse response:', error.message);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Connection error:', error.message);
  console.error('Make sure the backend server is running on http://localhost:8000');
  process.exit(1);
});

// Set timeout
req.setTimeout(5000, () => {
  console.error('❌ Connection timeout!');
  req.destroy();
  process.exit(1);
});