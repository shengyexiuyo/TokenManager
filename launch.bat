@echo off
chcp 65001 >nul
title Token Manager

echo Starting Token Manager...

:: Find Python interpreter
set PYTHON_PATH=

:: Check common Python locations
if exist "C:\Users\Administrator\python-sdk\python3.13.2\python.exe" (
    set PYTHON_PATH=C:\Users\Administrator\python-sdk\python3.13.2\python.exe
) else if exist "C:\Python313\python.exe" (
    set PYTHON_PATH=C:\Python313\python.exe
) else if exist "C:\Program Files\Python313\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python313\python.exe
) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe
)

:: Search for Python in PATH
if "%PYTHON_PATH%"=="" (
    for %%i in (python python3 python3.13) do (
        if not defined PYTHON_PATH (
            for /f "tokens=*" %%p in ('where %%i 2^>nul') do (
                if not defined PYTHON_PATH (
                    set "PYTHON_PATH=%%p"
                )
            )
        )
    )
)

if "%PYTHON_PATH%"=="" (
    echo.
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Found Python: %PYTHON_PATH%
echo.

:: Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Run the application
start "" "%PYTHON_PATH%" "%SCRIPT_DIR%token_manager.py"

exit
