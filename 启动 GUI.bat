@echo off
title Token Manager

cd /d "%~dp0"

echo ========================================
echo    Token Manager Launcher
echo ========================================
echo.

set PYTHON_EXE=C:\Users\Administrator\python-sdk\python3.13.2\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at: %PYTHON_EXE%
    echo.
    echo Searching for Python in system...
    where python >nul 2>&1
    if %errorlevel%==0 (
        for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
        echo [OK] Found Python: %PYTHON_EXE%
    ) else (
        echo [ERROR] Python not found. Please install Python.
        pause
        exit /b 1
    )
)

echo [INFO] Using Python: %PYTHON_EXE%
echo [INFO] Working directory: %cd%
echo.

if not exist "server.py" (
    echo [ERROR] server.py not found
    pause
    exit /b 1
)

echo [INFO] Starting server...
echo.

:: Start server in background
start "Token Manager Server" "%PYTHON_EXE%" server.py

:: Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 3 /nobreak >nul

:: Open browser
echo [INFO] Opening browser...
start http://localhost:5000

echo.
echo [INFO] Server started and browser opened.
echo [INFO] Close this window to stop the server.
echo.
pause