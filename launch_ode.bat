@echo off
TITLE Open Drama Engine Launcher
cd /d "D:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE"

:: 1. Check if backend server is already running on port 7860
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:7860/api/status' -TimeoutSec 1 -UseBasicParsing; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 (
    goto OPEN_BROWSER
)

:: 2. Boot app.py backend server silently in the background
start "" /b python app.py

:: 3. Wait until server responds on port 7860 (up to 15 seconds)
powershell -NoProfile -Command "$start = Get-Date; while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds(15)) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:7860/api/status' -TimeoutSec 1 -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Milliseconds 500 }; exit 1"

:OPEN_BROWSER
:: 4. Launch standalone Web Application window (Chrome or Edge App Mode)
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://127.0.0.1:7860
    exit /b 0
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --app=http://127.0.0.1:7860
    exit /b 0
)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:7860
    exit /b 0
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:7860
    exit /b 0
)

:: Fallback to default browser
start http://127.0.0.1:7860
exit /b 0
