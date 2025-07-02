// Test script to verify API imports
// This is just for verification and not meant to be run in production

// Import both styles to verify they work
import api, { apiMethods } from '../lib/api';

console.log('Testing API imports...');

// Test default export
console.log('Default export (api):', typeof api === 'object' ? 'OK' : 'FAILED');
console.log('api.getOutputs:', typeof api.getOutputs === 'function' ? 'OK' : 'FAILED');

// Test named export
console.log('Named export (apiMethods):', typeof apiMethods === 'object' ? 'OK' : 'FAILED');
console.log('apiMethods.getOutputs:', typeof apiMethods.getOutputs === 'function' ? 'OK' : 'FAILED');

// Verify they are the same object
console.log('api === apiMethods:', api === apiMethods ? 'OK (Same object)' : 'FAILED (Different objects)');

console.log('API import test complete!');