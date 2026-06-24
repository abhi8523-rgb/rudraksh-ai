@echo off
setlocal enabledelayedexpansion
title Neel AI - Startup
color 0A

:: Fix PATH for Node.js and Ollama
set "PATH=C:\Program Files\nodejs;%LOCALAPPDATA%\Programs\Ollama;C:\Program Files\Ollama;%PATH%"

:: Set project root (remove trailing backslash for safety)
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

:: Log file for debugging
set "LOGFILE=%ROOT%\startup.log"
echo [%date% %time%] Neel AI startup begin > "%LOGFILE%"

echo.
echo  ========================================
echo       NEEL AI - Sovereign Intelligence
echo  ========================================
echo.

:: ──────────────────────────────────────────
:: STEP 1: Check Ollama
:: ──────────────────────────────────────────
echo [1/5] Checking for Ollama...
echo [%time%] Step 1: Checking Ollama >> "%LOGFILE%"

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama not found in PATH.
    echo       Please install from: https://ollama.com/download
    echo.
    start https://ollama.com/download
    echo       After installing, restart your PC and run this again.
    echo [%time%] FAIL: Ollama not found >> "%LOGFILE%"
    goto :end_pause
)
echo       OK - Ollama found
echo [%time%] OK: Ollama found >> "%LOGFILE%"

:: ──────────────────────────────────────────
:: STEP 2: Start Ollama + pull models
:: ──────────────────────────────────────────
echo [2/5] Starting Ollama server...
echo [%time%] Step 2: Starting Ollama >> "%LOGFILE%"

tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if %errorlevel% neq 0 (
    start "" /MIN ollama serve
    timeout /t 5 /nobreak >nul
    echo       OK - Ollama started
) else (
    echo       OK - Ollama already running
)

echo       Checking models...
ollama list 2>nul | find "llama3.2:3b" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Downloading llama3.2:3b (~2GB, one-time)...
    ollama pull llama3.2:3b
)
echo       OK - Models ready
echo [%time%] OK: Ollama and models ready >> "%LOGFILE%"

:: ──────────────────────────────────────────
:: STEP 3: Setup backend
:: ──────────────────────────────────────────
echo [3/5] Setting up backend...
echo [%time%] Step 3: Backend setup >> "%LOGFILE%"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo       Python not found! Install from https://python.org
    echo       IMPORTANT: Check "Add to PATH" during install!
    start https://python.org/downloads
    echo [%time%] FAIL: Python not found >> "%LOGFILE%"
    goto :end_pause
)
echo       OK - Python found

cd /d "%ROOT%\backend"
if %errorlevel% neq 0 (
    echo       ERROR: Cannot find backend directory!
    echo [%time%] FAIL: backend dir not found >> "%LOGFILE%"
    goto :end_pause
)

if not exist "venv\Scripts\activate.bat" (
    echo       Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to create venv
        echo [%time%] FAIL: venv creation failed >> "%LOGFILE%"
        goto :end_pause
    )
)

call "venv\Scripts\activate.bat"
echo       Installing dependencies...
pip install -r requirements.txt -q 2>>"%LOGFILE%"
echo       OK - Backend ready
echo [%time%] OK: Backend deps installed >> "%LOGFILE%"

:: ──────────────────────────────────────────
:: STEP 4: Start backend
:: ──────────────────────────────────────────
echo [4/5] Starting backend server...
echo [%time%] Step 4: Starting backend >> "%LOGFILE%"

start "Neel-Backend" /MIN cmd /c "cd /d "%ROOT%\backend" && call "venv\Scripts\activate.bat" && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 4 /nobreak >nul
echo       OK - Backend at http://localhost:8001
echo [%time%] OK: Backend started >> "%LOGFILE%"

:: ──────────────────────────────────────────
:: STEP 5: Start frontend
:: ──────────────────────────────────────────
echo [5/5] Starting frontend...
echo [%time%] Step 5: Starting frontend >> "%LOGFILE%"

cd /d "%ROOT%\frontend"
if %errorlevel% neq 0 (
    echo       ERROR: Cannot find frontend directory!
    echo [%time%] FAIL: frontend dir not found >> "%LOGFILE%"
    goto :end_pause
)

if not exist "node_modules" (
    echo       Installing dependencies (first time, ~2 min)...
    call npm install >> "%LOGFILE%" 2>&1
    if %errorlevel% neq 0 (
        echo       ERROR: npm install failed! Check startup.log
        echo [%time%] FAIL: npm install failed >> "%LOGFILE%"
        goto :end_pause
    )
)

echo       Starting Next.js...
start "Neel-Frontend" /MIN cmd /c "set PATH=C:\Program Files\nodejs;%PATH% && cd /d "%ROOT%\frontend" && npm run dev"
timeout /t 8 /nobreak >nul
echo       OK - Frontend at http://localhost:3000
echo [%time%] OK: Frontend started >> "%LOGFILE%"

:: ──────────────────────────────────────────
:: DONE
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

timeout /t 2 /nobreak >nul
start http://localhost:3000

echo  DO NOT close this window while using Neel AI.
echo  Press any key here to STOP all services.
echo.
echo [%time%] Neel AI running, waiting for user >> "%LOGFILE%"
pause >nul

echo  Stopping services...
taskkill /F /FI "WINDOWTITLE eq Neel-Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Neel-Frontend*" >nul 2>&1
taskkill /F /IM "node.exe" >nul 2>&1
echo  Stopped. Goodbye!
echo [%time%] Services stopped >> "%LOGFILE%"
timeout /t 2 /nobreak >nul
goto :eof

:end_pause
echo.
echo  ========================================
echo   Setup incomplete. Fix the issue above,
echo   then double-click start.bat again.
echo  ========================================
echo.
echo  Check startup.log for details.
pause
goto :eof
