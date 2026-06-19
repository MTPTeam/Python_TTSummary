Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("Wscript.Shell")

' Get the folder where this VBScript is running
strPath = objFSO.GetParentFolderName(Wscript.ScriptFullName)

' Build the path to your batch file (Change "your_batch_file.bat" to your actual filename)
strBatch = """" & strPath & "\launch_TAIPAN_dev.bat" & """"

' Run the batch file with window style '0' (completely hidden)
objShell.Run strBatch, 0, False
