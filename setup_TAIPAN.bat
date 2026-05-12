@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo  TAIPAN Python Environment Setup
echo ============================================
echo.

echo Please ensure Python 3.12 is installed.
echo https://www.python.org/downloads/release/python-3129/
echo.

:: ── Detect Python ──────────────────────────────
echo Detecting Python 3.12...

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PY_ARGS=-3.12"
    echo   Using Python 3.12 via py launcher
) else (
    echo   Python 3.12 not found via py launcher.

    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set VER=%%v
        echo   Found Python !VER!

        echo !VER! | findstr /b "3.12" >nul
        if errorlevel 1 (
            echo ERROR: Python 3.12 required but found !VER!
            pause & exit /b 1
        )

        set "PYTHON_EXE=python"
        set "PY_ARGS="
    ) else (
        echo ERROR: Python not found.
        pause & exit /b 1
    )
)

echo.
echo Checking Python version...

"%PYTHON_EXE%" %PY_ARGS% -c "import sys; exit(0 if sys.version_info[:2]==(3,12) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.12 is required.
    "%PYTHON_EXE%" %PY_ARGS% --version
    pause & exit /b 1
)

echo   Python 3.12 confirmed.
echo.

:: ── Step 1: Create venv ───────────────────────
echo [1/4] Creating virtual environment...

if exist "%~dp0venv\Scripts\activate.bat" (
   echo   venv already exists, skipping creation.
) else (
   "%PYTHON_EXE%" %PY_ARGS% -m venv "%~dp0venv"
   if errorlevel 1 (
       echo ERROR: Failed to create virtual environment.
       pause & exit /b 1
   )
   echo   Virtual environment created.
)

echo.

:: ── Step 2: Install requirements.txt ──────────
echo [2/4] Installing packages from requirements.txt...

if not exist "%~dp0requirements.txt" (
   echo ERROR: requirements.txt not found in %~dp0
   pause & exit /b 1
)

"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
   echo WARNING: Some packages may have failed - check output above.
)

echo.

:: ── Step 3: Install pywin32 .whl ──────────────
echo [3/4] Installing pywin32...

set "WHL_PATH=%~dp0pywin32-312-cp312-cp312-win_amd64.whl"

if exist "%WHL_PATH%" (
   "%~dp0venv\Scripts\python.exe" -m pip install "%WHL_PATH%"
   if errorlevel 1 (
       echo WARNING: pywin32 install may have failed.
   )
) else (
   echo   WARNING: .whl file not found at %WHL_PATH%
   echo   Skipping - add it manually if needed.
)

echo.

:: ── Step 4: Install package in editable mode ──
echo [4/4] Installing TAIPAN as editable package...

set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

"%~dp0venv\Scripts\python.exe" -m pip install -e "%PROJECT_DIR%"
if errorlevel 1 (
   echo ERROR: Editable install failed.
   pause & exit /b 1
)

echo.

:: ── Verify ────────────────────────────────────
echo ============================================
echo  Verifying installation...
echo ============================================

"%~dp0venv\Scripts\python.exe" -c "import taipan" 2>&1
if errorlevel 1 (
   echo.
   echo FAILED: "import taipan" raised an error.
   pause & exit /b 1
)

echo.
echo  Setup complete! TAIPAN installed successfully.
echo  You can now run launch_TAIPAN.bat to start the app.
echo ============================================
echo.

pause