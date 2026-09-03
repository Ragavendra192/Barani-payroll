Set WshShell = CreateObject("WScript.Shell")

' Terminate any running Python process serving port 5081 or running app.py
WshShell.Run "cmd /c taskkill /f /im python.exe", 0, False

WScript.Sleep 1000
MsgBox "BHIPL Payroll Server stopped successfully.", 64, "BHIPL Payroll System"
