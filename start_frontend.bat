@echo off
echo ===================================================
echo   PRAVAH AI — Starting Vite + React Frontend
echo ===================================================
cd /d "%~dp0frontend"
echo Installing frontend dependencies...
call npm install
echo.
echo Starting Vite dev server on http://localhost:5173...
call npm run dev
pause
