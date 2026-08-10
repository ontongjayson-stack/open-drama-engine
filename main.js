/**
 * Open Drama Engine — Electron Main Process & Process Spawner (main.js)
 * Manages silent background Python/Node engine process binding to http://127.0.0.1:7860,
 * single-instance locking, and graceful app lifecycle termination.
 */

const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');

let mainWindow = null;
let serverProcess = null;

const PORT = 7860;
const SERVER_URL = `http://127.0.0.1:${PORT}`;

// 1. Single Instance Lock Guard
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  console.log('⚡ Another instance of Open Drama Engine is already running. Focusing primary window...');
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// 2. Silent Background Service Spawner
function startLocalEngineServer() {
  console.log(`⚡ Spawning Local Wan2GP Engine process silently on ${SERVER_URL}...`);

  const serverScript = path.join(__dirname, 'server.js');

  serverProcess = spawn('node', [serverScript], {
    cwd: __dirname,
    env: { ...process.env, PORT: PORT },
    stdio: ['ignore', 'pipe', 'pipe'] // Silent background process
  });

  serverProcess.stdout.on('data', (data) => {
    console.log(`[Engine Backend]: ${data.toString().trim()}`);
  });

  serverProcess.stderr.on('data', (data) => {
    console.warn(`[Engine Backend Notice]: ${data.toString().trim()}`);
  });

  serverProcess.on('exit', (code, signal) => {
    console.log(`[Engine Backend] Process exited with code ${code}, signal ${signal}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1480,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    title: 'Open Drama Engine v1.0 — AI Animation Studio',
    backgroundColor: '#090b0e',
    icon: path.join(__dirname, 'scifi_city_preview.jpg'),
    show: false, // Don't show until ready-to-show
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile('index.html');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  startLocalEngineServer();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 3. Graceful Background Process Termination
function cleanupBackgroundProcess() {
  if (serverProcess) {
    console.log('🛑 Cleanly terminating background Wan2GP engine process...');
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${serverProcess.pid} /T /F`);
      } else {
        serverProcess.kill('SIGTERM');
      }
    } catch (err) {
      console.warn('Process cleanup notice:', err.message);
    }
    serverProcess = null;
  }
}

app.on('before-quit', cleanupBackgroundProcess);

app.on('window-all-closed', () => {
  cleanupBackgroundProcess();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
