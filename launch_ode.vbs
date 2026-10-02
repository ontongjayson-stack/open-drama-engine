Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE"
WshShell.Run "cmd.exe /c launch_ode.bat", 0, False
