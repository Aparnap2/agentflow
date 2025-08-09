// Script to verify API methods are properly defined
import api, { apiMethods } from '../lib/api';

// List of expected methods
const expectedMethods = [
  'startConversation',
  'sendMessage',
  'approveConversation',
  'getAgentsStatus',
  'executeAgent',
  'getAgentPersonalities',
  'getOutputs',
  'generateReport',
  'getReport',
  'getPendingApprovals',
  'respondToApproval',
  'getPredictions',
  'getMemoryStats',
  'get',
  'post'
];

console.log('Verifying API methods...');

// Check default export (api)
console.log('\nChecking default export (api):');
let defaultExportMissing = [];
for (const method of expectedMethods) {
  if (typeof api[method] !== 'function') {
    defaultExportMissing.push(method);
  }
}

if (defaultExportMissing.length === 0) {
  console.log('✅ All methods present in default export');
} else {
  console.log('❌ Missing methods in default export:', defaultExportMissing);
}

// Check named export (apiMethods)
console.log('\nChecking named export (apiMethods):');
let namedExportMissing = [];
for (const method of expectedMethods) {
  if (typeof apiMethods[method] !== 'function') {
    namedExportMissing.push(method);
  }
}

if (namedExportMissing.length === 0) {
  console.log('✅ All methods present in named export');
} else {
  console.log('❌ Missing methods in named export:', namedExportMissing);
}

console.log('\nVerification complete!');