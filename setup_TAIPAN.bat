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
set "PYTHON_EXE="
set "PY_ARGS="
:: 1) Try Python launcher
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
   set "PYTHON_EXE=py"
   set "PY_ARGS=-3.12"
   echo   Using Python 3.12 via py launcher
   goto :python_found
)
echo   Python 3.12 not found via py launcher.
:: 2) Try system python
python --version >nul 2>&1
if not errorlevel 1 (
   for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set VER=%%v
   echo   Found system Python !VER!
   echo !VER! | findstr /b "3.12" >nul
   if not errorlevel 1 (
       set "PYTHON_EXE=python"
       set "PY_ARGS="
       echo   Using system Python 3.12
       goto :python_found
   ) else (
       echo   System Python !VER! is not 3.12 - skipping.
   )
) else (
   echo   No system Python found.
)
echo.
echo Automatic detection failed. Please provide the path to Python 3.12 manually.
:: 3) Manual fallback
echo Please enter full path to python.exe (must be Python 3.12)
echo Example:
echo   C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe
echo.
set /p PYTHON_EXE="Python path: "
if not exist "%PYTHON_EXE%" (
   echo ERROR: File not found.
   call :fatal
)
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
   echo ERROR: Invalid python executable.
   call :fatal
)
"%PYTHON_EXE%" -c "import sys; exit(0 if sys.version_info[:2]==(3,12) else 1)"
if errorlevel 1 (
   echo ERROR: Python 3.12 is required. Found:
   "%PYTHON_EXE%" --version
   call :fatal
)
set "PY_ARGS="
echo   Using manually specified Python.
:python_found
echo.
echo Checking Python version...
"%PYTHON_EXE%" %PY_ARGS% --version
echo   Python 3.12 confirmed.
echo.
:: ── Step 1: Create or validate venv ───────────
echo [1/5] Setting up virtual environment...
if exist "%~dp0venv\Scripts\activate.bat" (
   echo   Existing venv found. Verifying Python version...
   "%~dp0venv\Scripts\python.exe" -c "import sys; exit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>&1
   if errorlevel 1 (
       echo   ERROR: Existing venv is not Python 3.12.
       echo   Please delete the "venv" folder and re-run this script.
       call :fatal
   )
   echo   venv is Python 3.12, skipping creation.
) else (
   "%PYTHON_EXE%" %PY_ARGS% -m venv "%~dp0venv"
   if errorlevel 1 (
       echo ERROR: Failed to create virtual environment.
       call :fatal
   )
   echo   Virtual environment created.
)
echo.
:: ── Step 2: Upgrade pip ────────────────────────
echo [2/5] Upgrading pip...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
   echo   WARNING: pip upgrade failed. Continuing with existing pip version.
)
echo.
:: ── Step 3: Install requirements.txt ──────────
echo [3/5] Installing packages from requirements.txt...
if not exist "%~dp0requirements.txt" (
   echo ERROR: requirements.txt not found in %~dp0
   call :fatal
)
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
   echo WARNING: Some packages may have failed - check output above.
)
echo.
:: ── Step 4: Install pywin32 .whl ──────────────
echo [4/5] Installing pywin32...
set "WHL_PATH=%~dp0pywin32-311-cp312-cp312-win_amd64.whl"
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
:: ── Step 5: Install package in editable mode ──
echo [5/5] Installing TAIPAN as editable package...
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
"%~dp0venv\Scripts\python.exe" -m pip install -e "%PROJECT_DIR%"
if errorlevel 1 (
   echo ERROR: Editable install failed.
   call :fatal
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
   call :fatal
)
"%~dp0venv\Scripts\python.exe" -m pip check 2>&1
if errorlevel 1 (
  echo.
  echo WARNING: TAIPAN imported but one or more required packages may be missing or mismatched.
  echo   Run: venv\Scripts\pip check
  echo   to see details.
  echo.
)
echo.
echo  Setup complete! TAIPAN installed successfully.
echo  You can now run launch_TAIPAN.bat to start the app.
echo ============================================
echo.
call :maybe_pause
exit /b 0
:: ── Helpers ───────────────────────────────────
:fatal
call :maybe_pause
exit /b 1
:maybe_pause
for /f "tokens=2 delims=:" %%t in ('mode con 2^>nul ^| findstr /i "columns"') do (
   pause
   goto :eof
)
goto :eof