import os
import sys
import subprocess
from pathlib import Path

def install_desktop_shortcut():
    engine_dir = Path(r"D:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE")
    vbs_path = engine_dir / "launch_ode.vbs"
    icon_path = engine_dir / "ode_icon.ico"
    
    # Locate Desktop
    desktop_dir = Path(os.path.expanduser("~")) / "Desktop"
    if not desktop_dir.exists():
        # Fallback to OneDrive desktop if redirected
        onedrive_desktop = Path(os.path.expanduser("~")) / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            desktop_dir = onedrive_desktop
            
    shortcut_path = desktop_dir / "Open Drama Engine.lnk"
    
    # PowerShell script to create the WScript.Shell shortcut
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}')
    $Shortcut.TargetPath = 'wscript.exe'
    $Shortcut.Arguments = '"{str(vbs_path)}"'
    $Shortcut.WorkingDirectory = '{str(engine_dir)}'
    $Shortcut.IconLocation = '{str(icon_path)}, 0'
    $Shortcut.Description = 'Open Drama Engine - AI Studio Pro'
    $Shortcut.Save()
    """
    
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode == 0 and shortcut_path.exists():
        print(f"SUCCESS: Desktop shortcut created at: {shortcut_path}")
        return True, str(shortcut_path)
    else:
        err = res.stderr or "Failed to create shortcut"
        print(f"ERROR: {err}")
        return False, err

if __name__ == "__main__":
    success, msg = install_desktop_shortcut()
    sys.exit(0 if success else 1)
