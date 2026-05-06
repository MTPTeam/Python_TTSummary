@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo ============================================
echo  TAIPAN Python Environment Setup
echo ============================================
echo.
:: ── Get username ──────────────────────────────
set /p USERNAME="Enter your username (e.g. r123456): "
set PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYTHON_EXE%" (
   echo.
   echo ERROR: Python 3.12 not found at:
   echo   %PYTHON_EXE%
   echo.
   echo Check your username is correct and Python 3.12 is installed.
   pause & exit /b 1
)
echo   Found: %PYTHON_EXE%
echo.
:: ── Step 1: Create venv ───────────────────────
echo [1/4] Creating virtual environment...
if exist "%~dp0venv\Scripts\activate.bat" (
   echo   venv already exists, skipping creation.
) else (
   "%PYTHON_EXE%" -m venv "%~dp0venv"
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
set WHL_PATH=C:\Python_TTSummary\pywin32-311-cp312-cp312-win_amd64.whl
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
"%~dp0venv\Scripts\python.exe" -m pip install -e "%~dp0"
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
   echo FAILED: "import taipan" raised an error. See above for details.
   pause & exit /b 1
)
echo.
echo  Setup complete! TAIPAN installed successfully.
echo  You can now run launch_TAIPAN.bat to start the app.
echo ============================================
echo.
pause