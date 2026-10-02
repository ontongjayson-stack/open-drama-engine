@echo off
TITLE Open Drama Engine Studio Pro Launcher
cd /d "D:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE"

echo =========================================================================
echo   OPEN DRAMA ENGINE -- AI STUDIO PRO
echo =========================================================================
echo [1/2] Verifying Local ComfyUI GPU Render Engine (127.0.0.1:8188)...

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 2 -UseBasicParsing; Write-Host '[OK] Local ComfyUI GPU Engine is running.' -ForegroundColor Green } catch { Write-Host '[LAUNCHING] Booting ComfyUI Render Engine in background...' -ForegroundColor Yellow; Start-Process -FilePath 'cmd.exe' -ArgumentList '/c cd /d \"D:\AI DEVELOPMENTS\ComfyUI\" && call .\venv\Scripts\activate && python main.py --listen 127.0.0.1 --port 8188 --fp32-vae --lowvram --preview-method auto' -WindowStyle Minimized }"

echo [2/2] Launching Open Drama Engine AI Studio Pro Dashboard...
echo Dashboard will open at: http://127.0.0.1:7860
python app.py
pause