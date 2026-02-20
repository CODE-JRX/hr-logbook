Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "run.bat" & chr(34), 0, False
Set WshShell = Nothing
