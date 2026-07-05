@echo off
echo ================================================
echo  NexusOps - Autonomous DevOps Intelligence
echo  100%% Free Stack: Groq + GitHub API + LangGraph
echo ================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (echo [ERROR] Python not found. Install Python 3.11+ & exit /b 1)

findstr /C:"your-groq-api-key-here" backend\.env >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Add your free Groq API key to backend\.env
    echo           Get it free at: https://console.groq.com
)
findstr /C:"your-github-token-here" backend\.env >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Add your GitHub token to backend\.env
    echo           Get it free at: https://github.com/settings/tokens
    echo.
)

echo [1/3] Setting up backend...
if not exist backend\venv (
    python -m venv backend\venv
)
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt -q

mkdir backend\data\chroma 2>nul

echo [2/3] Installing frontend dependencies...
cd frontend
call npm install --silent
cd ..

echo [3/3] Starting services...
start "NexusOps Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "NexusOps Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================
echo  NexusOps is starting!
echo  Backend:  http://localhost:8000/docs
echo  Frontend: http://localhost:3000
echo.
echo  Add a GitHub repo in the UI to begin analysis.
echo ================================================
