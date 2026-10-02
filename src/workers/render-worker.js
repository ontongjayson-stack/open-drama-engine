require('../utils/env-loader');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const args = require('minimist')(process.argv.slice(2));
const root = path.resolve(__dirname, '../..');
const timeline = path.resolve(args.timeline || path.join(root, 'temp/compiled_timeline.json'));
if (!fs.existsSync(timeline)) { console.error('Timeline file is missing: ' + timeline); process.exit(1); }
const raw = JSON.parse(fs.readFileSync(timeline, 'utf8'));
const title = (raw.timeline || raw.data || raw).project_metadata?.title || 'Anime_story';
const output = path.join(path.resolve(args.output || path.join(root, 'exports')), title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 100) + '.mp4');
const child = spawn(process.env.ODE_PYTHON_PATH || 'python', ['-B', path.join(root, 'engine_bridge.py'), '--action', 'render_timeline', '--payload', timeline, '--out', output], { cwd: root, windowsHide: true, stdio: 'inherit' });
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('close', code => {
  if (code !== 0 || !fs.existsSync(output) || fs.statSync(output).size < 1024) { console.error('Rendering failed; no verified film was exported.'); process.exitCode = 1; }
  else console.log('Verified story export: ' + output);
});
