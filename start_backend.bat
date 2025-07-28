@echo off
echo ========================================
echo Starting Altona Village Backend Server...
echo ========================================

REM Change to the backend source directory
cd /d "c:\Altona_Village_CMS\altona_village_cms\src"

REM Check if Python virtual environment exists
if not exist "C:\Altona_Village_CMS\.venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Start the backend server
echo Starting Flask server...
C:\Altona_Village_CMS\.venv\Scripts\python.exe main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Backend server stopped with error code %errorlevel%
    pause
)
