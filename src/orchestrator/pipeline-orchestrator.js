require('../utils/env-loader');
const { spawn } = require('child_process');
const path = require('path');
const args = require('minimist')(process.argv.slice(2));
const prompt = args.prompt || args._[0];
if (!prompt) { console.error('Supply a story prompt: npm run engine:run -- --prompt="Your story" --duration=300'); process.exit(1); }
const root = path.resolve(__dirname, '../..');
const payload = { topic: prompt, genre: 'Anime', duration: Number(args.duration || 300), characterAnchor: args.character || '', provider: args.provider || 'auto' };
const child = spawn(process.env.ODE_PYTHON_PATH || 'python', ['-B', path.join(root, 'engine_bridge.py'), '--action', 'orchestrate', '--payload', JSON.stringify(payload)], { cwd: root, windowsHide: true, stdio: 'inherit' });
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('close', code => { process.exitCode = code === 0 ? 0 : 1; });
