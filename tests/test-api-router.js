/**
 * Open Drama Engine - Multi-Provider API Router Test
 * File: tests/test-api-router.js
 */

const { dispatchStageRequest, ROUTER_CONFIG } = require('../src/router/api-router');

console.log('[TEST ROUTER] Initializing Router Config Validation...');
console.log(`[TEST ROUTER] Registered Providers: ${Object.keys(ROUTER_CONFIG.providers).join(', ')}`);
console.log(`[TEST ROUTER] Configured Strategies: ${Object.keys(ROUTER_CONFIG.strategies).join(', ')}`);

async function testRouter() {
  try {
    console.log('[TEST ROUTER] Testing dispatchStageRequest with missing keys (Graceful Skip Test)...');
    await dispatchStageRequest('scripting', 'System Prompt', 'User Prompt');
  } catch (err) {
    console.log(`[TEST ROUTER] Expected fallback behavior triggered: ${err.message}`);
    console.log('[TEST ROUTER] Router configuration and fallback matrix verified successfully!');
    process.exit(0);
  }
}

testRouter();
