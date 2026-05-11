@echo off
setlocal

cd /d "%~dp0"

echo ============================================
echo TAIPAN Updater
echo Reminder: Pull latest code via GitHub Desktop first
echo ============================================
echo.

:: Check venv
if not exist "%~dp0venv\Scripts\python.exe" (
    echo ERROR: venv not found.
    echo Please run setup_TAIPAN.bat first.
    pause & exit /b 1
)

set PYTHON_EXE=%~dp0venv\Scripts\python.exe

:: Step 1: Upgrade pip (safe and local)
echo [1/3] Upgrading pip...
"%PYTHON_EXE%" -m pip install --upgrade pip >nul 2>&1

:: Step 2: Update dependencies
echo.
echo [2/3] Updating dependencies...
if exist "%~dp0requirements.txt" (
    "%PYTHON_EXE%" -m pip install --upgrade -r "%~dp0requirements.txt"
) else (
    echo WARNING: requirements.txt missing
)

:: Step 3: Reinstall project
echo.
echo [3/3] Reinstalling TAIPAN...
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

"%PYTHON_EXE%" -m pip install -e "%PROJECT_DIR%"

:: Verify
echo.
echo Verifying...
"%PYTHON_EXE%" -c "import taipan" 2>nul
if errorlevel 1 (
    echo ERROR: TAIPAN import failed
    pause & exit /b 1
)

echo.
echo Update complete
echo (Reminder: Pull latest code via GitHub Desktop first)
echo ============================================
pause