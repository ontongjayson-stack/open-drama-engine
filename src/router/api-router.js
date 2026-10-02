require('../utils/env-loader');
const axios = require('axios');

// Provider Configuration Registry (Configured for $0.00 Free Tier)
const ROUTER_CONFIG = {
  providers: {
    openrouter: {
      name: 'OpenRouter Free Router',
      baseUrl: 'https://openrouter.ai/api/v1/chat/completions',
      apiKeyEnv: 'OPENROUTER_API_KEY',
      defaultModel: 'openrouter/free'
    },
    ollama: {
      name: 'Local Ollama Engine',
      baseUrl: 'http://localhost:11434/api/chat',
      apiKeyEnv: null,
      defaultModel: 'llama3'
    }
  },
  strategies: {
    scripting: {
      primary: 'openrouter',
      fallbacks: ['ollama'],
      timeoutMs: 15000
    },
    asset_prompts: {
      primary: 'openrouter',
      fallbacks: ['ollama'],
      timeoutMs: 12000
    },
    timeline_assembly: {
      primary: 'openrouter',
      fallbacks: ['ollama'],
      timeoutMs: 10000
    }
  },
  maxRetriesPerProvider: 1
};

async function dispatchStageRequest(stage, systemPrompt, userPrompt) {
  const strategy = ROUTER_CONFIG.strategies[stage];
  if (!strategy) {
    throw new Error(`[API ROUTER] Invalid routing stage: "${stage}"`);
  }

  const providerChain = [strategy.primary, ...strategy.fallbacks];
  console.log(`[API ROUTER] Executing Stage: [${stage.toUpperCase()}] | Priority Chain: ${providerChain.join(' -> ')}`);

  for (const providerKey of providerChain) {
    const provider = ROUTER_CONFIG.providers[providerKey];
    const apiKey = provider.apiKeyEnv ? process.env[provider.apiKeyEnv] : null;

    if (provider.apiKeyEnv && !apiKey) {
      console.warn(`[API ROUTER] Skipping ${provider.name}: ${provider.apiKeyEnv} missing in .env`);
      continue;
    }

    try {
      console.log(`[API ROUTER] Attempting call via Provider: ${provider.name} (${provider.defaultModel})`);

      const payload = providerKey === 'ollama' ? {
        model: provider.defaultModel,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        stream: false,
        format: 'json'
      } : {
        model: provider.defaultModel,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        response_format: { type: 'json_object' }
      };

      const headers = { 'Content-Type': 'application/json' };
      if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

      const response = await axios.post(provider.baseUrl, payload, {
        headers,
        timeout: strategy.timeoutMs
      });

      const content = response.data?.choices?.[0]?.message?.content || response.data?.message?.content || response.data;
      const parsedJson = typeof content === 'string' ? JSON.parse(content) : content;

      console.log(`[API ROUTER] SUCCESS via Provider: ${provider.name}`);
      return parsedJson;

    } catch (error) {
      const statusCode = error.response ? error.response.status : error.code;
      console.warn(`[API ROUTER] Failover Event | Stage: ${stage} | Provider: ${provider.name} | Error: ${statusCode}`);
    }
  }

  console.warn(`[API ROUTER] All cloud/local providers failed for [${stage}]. Executing built-in Local Generator Fallback.`);

  // Return full mock timeline on stage 4 fallback to prevent render crash
  if (stage === 'timeline_assembly') {
    return {
      project_metadata: {
        title: "Headless Sequence: Local Fallback",
        fps: 30,
        resolution: { width: 1920, height: 1080 },
        duration_frames: 300
      },
      tracks: {
        backgrounds: [{ id: "bg_default", asset_path: "assets/bg/default.png", frame_start: 0, frame_end: 300, transform: { scale: 1.0, position: { x: 0, y: 0 } } }],
        character_layers: [],
        props: [],
        audio: []
      }
    };
  }

  return { status: "fallback_generated", stage: stage, timestamp: Date.now() };
}

module.exports = { dispatchStageRequest, ROUTER_CONFIG };