/**
 * Open Drama Engine - Timeline Runner & Integration Test Suite
 * File: tests/test-timeline-runner.js
 * 
 * Validates Headless Open Drama Timeline JSON and invokes render-worker.js.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const tempDir = path.join(__dirname, '../temp');
const exportDir = path.join(__dirname, '../exports');
const mockTimelinePath = path.join(tempDir, 'mock_timeline.json');

// Ensure required directories exist
if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
if (!fs.existsSync(exportDir)) fs.mkdirSync(exportDir, { recursive: true });

// 1. Construct Mock Headless Timeline Payload
const mockTimeline = {
  project_metadata: {
    title: "Test Episode: The Anti-Gravity Spark",
    fps: 30,
    resolution: { width: 1920, height: 1080 },
    duration_frames: 300
  },
  tracks: {
    backgrounds: [
      {
        id: "bg_cyber_city",
        asset_path: "assets/bg/cyber_city.png",
        frame_start: 0,
        frame_end: 300,
        transform: {
          scale: 1.0,
          position: { x: 0, y: 0 }
        }
      }
    ],
    character_layers: [
      {
        character_id: "detective_rig",
        layer_order: 1,
        frame_start: 0,
        frame_end: 300,
        rig_manifest: "assets/characters/detective/rig.json",
        keyframes: [
          {
            frame: 0,
            position: { x: -100, y: 0 },
            scale: { x: 1.0, y: 1.0 },
            rotation: 0,
            easing: "ease_in_out_quad"
          },
          {
            frame: 150,
            position: { x: 450, y: 0 },
            scale: { x: 1.0, y: 1.0 },
            rotation: 0,
            easing: "linear"
          }
        ],
        animation_states: [
          { frame_start: 0, frame_end: 150, state: "walk" },
          { frame_start: 151, frame_end: 300, state: "speak" }
        ],
        lip_sync: {
          audio_track_id: "vox_det_01",
          viseme_map_path: "assets/characters/detective/visemes_01.json"
        }
      }
    ],
    props: [],
    audio: [
      {
        id: "vox_det_01",
        type: "dialogue",
        file_path: "assets/audio/vox_det_01.wav",
        frame_start: 151,
        volume: 1.0,
        fade_in_frames: 0,
        fade_out_frames: 0
      },
      {
        id: "bgm_synth",
        type: "music",
        file_path: "assets/audio/bgm_synth.mp3",
        frame_start: 0,
        volume: 0.3,
        fade_in_frames: 15,
        fade_out_frames: 30
      }
    ]
  }
};

// 2. Schema Validation Assertion Logic
function validateTimelineSchema(payload) {
  console.log('[TEST RUNNER] Validating Headless Timeline JSON Schema...');
  
  if (!payload.project_metadata || !payload.project_metadata.title) {
    throw new Error('Schema Violation: Missing project_metadata.title');
  }
  if (!payload.project_metadata.fps || !payload.project_metadata.duration_frames) {
    throw new Error('Schema Violation: Missing FPS or duration_frames setting');
  }
  if (!payload.tracks || !Array.isArray(payload.tracks.character_layers)) {
    throw new Error('Schema Violation: Missing character_layers track array');
  }

  console.log('[TEST RUNNER] Schema Validation Status: PASSED');
}

// 3. Execution Routine
async function runIntegrationTest() {
  try {
    // Validate schema in memory
    validateTimelineSchema(mockTimeline);

    // Write mock timeline to disk
    fs.writeFileSync(mockTimelinePath, JSON.stringify(mockTimeline, null, 2));
    console.log(`[TEST RUNNER] Mock timeline written to ${mockTimelinePath}`);

    // Spawn render-worker.js child process
    const workerScript = path.join(__dirname, '../src/workers/render-worker.js');
    console.log(`[TEST RUNNER] Spawning Render Worker: ${workerScript}`);

    const workerProcess = spawn('node', [
      workerScript,
      `--timeline=${mockTimelinePath}`,
      `--output=${exportDir}`
    ]);

    workerProcess.stdout.on('data', (data) => {
      process.stdout.write(`[WORKER LOG] ${data.toString()}`);
    });

    workerProcess.stderr.on('data', (data) => {
      process.stderr.write(`[WORKER ERROR] ${data.toString()}`);
    });

    workerProcess.on('close', (code) => {
      if (code === 0) {
        console.log('[TEST RUNNER] Integration Test Execution: SUCCESS');
      } else {
        console.error(`[TEST RUNNER] Integration Test Execution FAILED with exit code ${code}`);
        process.exit(1);
      }
    });

  } catch (err) {
    console.error('[TEST RUNNER] Fatal Test Error:', err.message);
    process.exit(1);
  }
}

runIntegrationTest();
