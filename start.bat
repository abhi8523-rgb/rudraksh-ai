@echo off
title Neel AI - Startup
color 0A
echo.
echo  ========================================
echo       NEEL AI - Sovereign Intelligence
echo  ========================================
echo.

:: Fix PATH - ensure common tool directories are included
set "PATH=C:\Program Files\nodejs;%LOCALAPPDATA%\Programs\Ollama;C:\Program Files\Ollama;%PATH%"

:: ──────────────────────────────────────────
:: STEP 1: Check for Ollama
:: ──────────────────────────────────────────
echo [1/5] Checking for Ollama...

where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo       OK - Ollama found
    goto :ollama_ready
)

:: Ollama not found
echo.
echo  ========================================
echo   Ollama is NOT installed on your system.
echo   Ollama is the AI engine that runs the
echo   language models locally on your PC.
echo  ========================================
echo.
echo   Opening the download page now...
start https://ollama.com/download
echo.
echo   1. Download and install Ollama
echo   2. Restart your computer
echo   3. Run this script again
echo.
pause
exit /b 0

:ollama_ready

:: ──────────────────────────────────────────
:: STEP 2: Start Ollama server + pull models
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

echo       Checking AI models...
ollama list 2>nul | find "llama3.2:3b" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Downloading llama3.2:3b model (~2GB, one-time)...
    ollama pull llama3.2:3b
    echo       OK - llama3.2:3b downloaded
) else (
    echo       OK - llama3.2:3b ready
)

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
:: STEP 3: Check Python + setup backend
:: ──────────────────────────────────────────
echo [3/5] Setting up backend...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Python is NOT installed!
    echo   Download from: https://python.org
    echo   IMPORTANT: Check "Add to PATH" during install!
    start https://python.org/downloads
    echo.
    pause
    exit /b 0
)

cd /d "%NEEL_ROOT%backend"
if not exist "venv" (
    echo       Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo   ERROR: Failed to create venv. Need Python 3.11+
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
start "Neel-Backend" /MIN cmd /k "set PATH=C:\Program Files\nodejs;%PATH% && cd /d %NEEL_ROOT%backend && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 4 >nul
echo       OK - Backend running at http://localhost:8001

:: ──────────────────────────────────────────
:: STEP 5: Check Node.js + start frontend
:: ──────────────────────────────────────────
echo [5/5] Starting frontend...

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Node.js is NOT installed!
    echo   Download from: https://nodejs.org (LTS version)
    start https://nodejs.org
    echo.
    echo   Install Node.js, then run this script again.
    pause
    exit /b 0
)

:: Verify npm is accessible
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo       npm not in PATH, using direct path...
    set "NPM_CMD=C:\Program Files\nodejs\npm.cmd"
) else (
    set "NPM_CMD=npm"
)

cd /d "%NEEL_ROOT%frontend"

if not exist "node_modules" (
    echo       Installing frontend dependencies (first time, ~2 min)...
    call "%NPM_CMD%" install
    if %errorlevel% neq 0 (
        echo.
        echo   ERROR: npm install failed!
        echo   Try running manually:
        echo     cd "%NEEL_ROOT%frontend"
        echo     npm install
        echo.
        pause
        exit /b 1
    )
    echo       OK - Dependencies installed
) else (
    echo       OK - Dependencies already installed
)

echo       Starting Next.js dev server...
start "Neel-Frontend" /MIN cmd /k "set PATH=C:\Program Files\nodejs;%PATH% && cd /d %NEEL_ROOT%frontend && npm run dev"
timeout /t 8 >nul
echo       OK - Frontend starting at http://localhost:3000

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
