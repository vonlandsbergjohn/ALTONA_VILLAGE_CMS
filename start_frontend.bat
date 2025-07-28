@echo off
echo ========================================
echo Starting Altona Village Frontend Server...
echo ========================================

REM Change to the frontend directory
cd /d "c:\Altona_Village_CMS\altona-village-frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo WARNING: node_modules not found!
    echo Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the frontend development server
echo Starting Vite development server...
npm run dev

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Frontend server stopped with error code %errorlevel%
    pause
)
