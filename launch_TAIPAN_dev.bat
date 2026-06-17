@echo off
:: Change directory to where the .bat file is located
cd /d "%~dp0"

:: Set PYTHONPATH relative to the .bat location
set PYTHONPATH=%~dp0src

:: Run python from the local venv relative to the .bat location
"%~dp0venv\Scripts\python.exe" "%~dp0src\taipan\gui\launch.py"

