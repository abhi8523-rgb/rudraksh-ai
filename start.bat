@echo off
title 🔱 Rudraksh AI — Startup
color 0A
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║          🔱 RUDRAKSH AI — STARTUP            ║
echo  ║      Sovereign Intelligence Suite            ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Check if Ollama is installed
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Ollama not found! Install from: https://ollama.com
    echo     After installing, run this script again.
    pause
    exit /b 1
)

:: Start Ollama server if not running
echo [1/5] Starting Ollama server...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %errorlevel% neq 0 (
    start /MIN ollama serve
    timeout /t 3 >nul
    echo       ✅ Ollama started
) else (
    echo       ✅ Ollama already running
)

:: Pull default model if not present
echo [2/5] Checking for AI models...
ollama list | find "llama3.2:3b" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Pulling llama3.2:3b (this may take a few minutes)...
    ollama pull llama3.2:3b
) else (
    echo       ✅ llama3.2:3b ready
)

:: Pull embedding model
ollama list | find "nomic-embed-text" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Pulling nomic-embed-text for RAG...
    ollama pull nomic-embed-text
) else (
    echo       ✅ nomic-embed-text ready
)

:: Install backend dependencies
echo [3/5] Setting up backend...
cd backend
if not exist "venv" (
    python -m venv venv
    echo       Created virtual environment
)
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
echo       ✅ Backend ready

:: Start backend
echo [4/5] Starting backend server on port 8001...
start /MIN cmd /c "cd /d %~dp0\backend && venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 >nul
echo       ✅ Backend running at http://localhost:8001

:: Start frontend
echo [5/5] Starting frontend...
cd ..\frontend
if not exist "node_modules" (
    echo       Installing dependencies (first time only)...
    npm install
)
start /MIN cmd /c "cd /d %~dp0\frontend && npm run dev"
timeout /t 5 >nul
echo       ✅ Frontend running at http://localhost:3000

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     🔱 RUDRAKSH AI IS NOW RUNNING!           ║
echo  ║                                              ║
echo  ║     Frontend: http://localhost:3000           ║
echo  ║     Backend:  http://localhost:8001           ║
echo  ║     API Docs: http://localhost:8001/docs      ║
echo  ║                                              ║
echo  ║     Sovereign: abhi8523@gmail.com             ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo Opening Rudraksh AI in your browser...
timeout /t 2 >nul
start http://localhost:3000

echo.
echo Press any key to STOP all services...
pause >nul

:: Cleanup
taskkill /F /IM "node.exe" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq uvicorn*" >nul 2>&1
echo Services stopped. Goodbye! 🔱
