const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
let backend;
let window;
const url = 'http://127.0.0.1:7860';
if (!app.requestSingleInstanceLock()) app.quit();
app.on('second-instance', () => { if (window) { window.show(); window.focus(); } });

function ready() {
  return new Promise(resolve => {
    const request = http.get(url + '/api/status', response => { response.resume(); resolve(response.statusCode === 200); });
    request.setTimeout(3000, () => { request.destroy(); resolve(false); });
    request.on('error', () => resolve(false));
  });
}

app.whenReady().then(async () => {
  if (!await ready()) {
    backend = spawn(process.env.ODE_PYTHON_PATH || 'python', ['-B', path.join(__dirname, 'app.py')], { cwd: __dirname, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
    let errors = '';
    backend.stderr.on('data', data => { errors = (errors + data.toString()).slice(-3000); });
    backend.stdout.on('data', data => console.log(data.toString()));
    backend.on('error', error => { dialog.showErrorBox('Python could not start', error.message + '\nInstall the project requirements or set ODE_PYTHON_PATH.'); app.quit(); });
    let online = false;
    for (let attempt = 0; attempt < 60; attempt++) {
      if (await ready()) { online = true; break; }
      if (backend.exitCode !== null) break;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    if (!online) { dialog.showErrorBox('Story studio could not start', errors || 'The dashboard did not become ready. Check Python and requirements.txt.'); app.quit(); return; }
  }
  window = new BrowserWindow({ width: 1480, height: 940, minWidth: 900, minHeight: 700, title: 'Open Drama Engine — Anime Story Studio', icon: path.join(__dirname, 'ode_icon.ico'), webPreferences: { nodeIntegration: false, contextIsolation: true } });
  window.setMenuBarVisibility(false);
  window.loadURL(url);
});
app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => { if (backend) backend.kill(); });
