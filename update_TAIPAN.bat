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

:: Check if requirements.txt exists
if not exist "%~dp0requirements.txt" (
    echo WARNING: requirements.txt missing
    goto :VERIFY
)

echo Checking if virtual environment matches requirements.txt...

:: Run a dry-run install.
"%PYTHON_EXE%" -m pip install --dry-run -r "%~dp0requirements.txt" 2>&1 | findstr /i "Would install Would update" >nul

:: If findstr finds nothing, everything is satisfied. Skip EVERYTHING and go to verification.
if errorlevel 1 (
    echo All dependencies are already satisfied. Skipping update.
    goto :VERIFY
)

echo.
echo Found missing or outdated dependencies!
echo.

:: Step 1: Upgrade pip
echo [1/3] Upgrading pip...
"%PYTHON_EXE%" -m pip install --upgrade pip >nul 2>&1

:: Step 2: Update dependencies
echo [2/3] Installing/updating missing libraries...
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt"

:: Step 3: Reinstall project (Only runs if dependencies actually changed)
echo.
echo [3/3] Reinstalling TAIPAN...
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

"%PYTHON_EXE%" -m pip install -e "%PROJECT_DIR%"

:VERIFY
:: Verify
echo.
echo Verifying...
"%PYTHON_EXE%" -c "import taipan" 2>nul
if errorlevel 1 (
    echo ERROR: TAIPAN import failed
    pause & exit /b 1
)

echo.
echo Update complete (No changes needed!)
echo ============================================
pause
