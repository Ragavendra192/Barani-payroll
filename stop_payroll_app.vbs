Set WshShell = CreateObject("WScript.Shell")

' Terminate any running Python process serving port 5006 or running app.py
WshShell.Run "cmd /c taskkill /f /t /im python.exe /im pythonw.exe", 0, False

WScript.Sleep 1000
MsgBox "BHIPL Payroll Server stopped successfully.", 64, "BHIPL Payroll System"
