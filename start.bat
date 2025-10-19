@echo off
echo ================================================
echo   Starting Smart E-Commerce Search System
echo ================================================
echo.
echo Starting Backend API...
echo.
start python app.py
timeout /t 3 /nobreak >nul
echo.
echo Starting Frontend...
echo.
start index.html
echo.
echo ================================================
echo   SYSTEM STARTED!
echo ================================================
echo.
echo Backend: http://127.0.0.1:5000
echo Frontend: Open in your browser
echo.
pause


