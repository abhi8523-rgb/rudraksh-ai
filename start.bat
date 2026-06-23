@echo off
title Neel AI - Startup
color 0A
echo.
echo  ========================================
echo       NEEL AI - Sovereign Intelligence
echo  ========================================
echo.

:: ──────────────────────────────────────────
:: STEP 1: Check for Ollama
:: ──────────────────────────────────────────
echo [1/5] Checking for Ollama...

:: Check PATH first
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo       OK - Ollama found in PATH
    goto :ollama_ready
)

:: Check common install locations
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
    echo       OK - Ollama found in AppData
    goto :ollama_ready
)
if exist "C:\Program Files\Ollama\ollama.exe" (
    set "PATH=C:\Program Files\Ollama;%PATH%"
    echo       OK - Ollama found in Program Files
    goto :ollama_ready
)
if exist "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" (
    set "PATH=%USERPROFILE%\AppData\Local\Programs\Ollama;%PATH%"
    echo       OK - Ollama found in user AppData
    goto :ollama_ready
)

:: Ollama not found anywhere
echo.
echo  ========================================
echo   Ollama is NOT installed on your system.
echo   Ollama is the AI engine that runs the
echo   language models locally on your PC.
echo  ========================================
echo.
echo   Opening the download page now...
echo.
start https://ollama.com/download
echo   Please follow these steps:
echo     1. Download Ollama from the page that just opened
echo     2. Install it (just run the installer, click Next)
echo     3. RESTART this script after installation
echo.
echo   NOTE: After installing, you may need to restart
echo   your computer for Ollama to be in your PATH.
echo.
echo  ========================================
pause
exit /b 0

:ollama_ready

:: ──────────────────────────────────────────
:: STEP 2: Start Ollama server if not running
:: ──────────────────────────────────────────
echo [2/5] Starting Ollama server...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %errorlevel% neq 0 (
    start "Ollama-Server" /MIN ollama serve
    timeout /t 5 >nul
    echo       OK - Ollama server started
) else (
    echo       OK - Ollama already running
)

:: Pull default model if not present
echo       Checking AI models...
ollama list 2>nul | find "llama3.2:3b" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Downloading llama3.2:3b model...
    echo       This is a one-time download of ~2GB, please wait...
    ollama pull llama3.2:3b
    echo       OK - llama3.2:3b downloaded
) else (
    echo       OK - llama3.2:3b ready
)

:: Pull embedding model
ollama list 2>nul | find "nomic-embed-text" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Downloading nomic-embed-text for RAG...
    ollama pull nomic-embed-text
    echo       OK - nomic-embed-text downloaded
) else (
    echo       OK - nomic-embed-text ready
)

:: Store the root directory
set "NEEL_ROOT=%~dp0"

:: ──────────────────────────────────────────
:: STEP 3: Check for Python
:: ──────────────────────────────────────────
echo [3/5] Setting up backend...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Python is NOT installed!
    echo   Download from: https://python.org
    echo   Make sure to check "Add to PATH" during install.
    echo.
    start https://python.org/downloads
    pause
    exit /b 0
)

cd /d "%NEEL_ROOT%backend"
if not exist "venv" (
    echo       Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo   ERROR: Failed to create virtual environment.
        echo   Make sure Python 3.11+ is installed.
        pause
        exit /b 1
    )
    echo       OK - Virtual environment created
)
call venv\Scripts\activate.bat
echo       Installing backend dependencies (may take a minute)...
pip install -r requirements.txt -q 2>nul
echo       OK - Backend ready

:: ──────────────────────────────────────────
:: STEP 4: Start backend server
:: ──────────────────────────────────────────
echo [4/5] Starting backend server on port 8001...
start "Neel-Backend" /MIN cmd /k "cd /d %NEEL_ROOT%backend && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 4 >nul
echo       OK - Backend running at http://localhost:8001

:: ──────────────────────────────────────────
:: STEP 5: Check for Node.js and start frontend
:: ──────────────────────────────────────────
echo [5/5] Starting frontend...

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Node.js is NOT installed!
    echo   Download from: https://nodejs.org
    echo.
    start https://nodejs.org
    echo   Install Node.js, then run this script again.
    echo   (The backend is already running on port 8001)
    pause
    exit /b 0
)

cd /d "%NEEL_ROOT%frontend"
if not exist "node_modules" (
    echo       Installing frontend dependencies (first time only)...
    echo       This may take 2-3 minutes, please wait...
    call npm install
)
start "Neel-Frontend" /MIN cmd /k "cd /d %NEEL_ROOT%frontend && npm run dev"
timeout /t 8 >nul
echo       OK - Frontend running at http://localhost:3000

:: ──────────────────────────────────────────
:: ALL DONE
:: ──────────────────────────────────────────
echo.
echo  ========================================
echo      NEEL AI IS NOW RUNNING!
echo.
echo      Dashboard: http://localhost:3000
echo      Backend:   http://localhost:8001
echo      API Docs:  http://localhost:8001/docs
echo.
echo      Login:     abhi8523@gmail.com
echo      Password:  neel2026
echo  ========================================
echo.
echo  Opening Neel AI in your browser...
timeout /t 2 >nul
start http://localhost:3000

echo.
echo  ========================================
echo   Neel AI is running in the background.
echo   DO NOT close this window while using it.
echo.
echo   When you are done, press any key here
echo   to stop all services.
echo  ========================================
pause >nul

:: Cleanup
echo.
echo  Stopping services...
taskkill /F /FI "WINDOWTITLE eq Neel-Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Neel-Frontend*" >nul 2>&1
taskkill /F /IM "node.exe" >nul 2>&1
echo  All services stopped. Goodbye!
timeout /t 2 >nul
