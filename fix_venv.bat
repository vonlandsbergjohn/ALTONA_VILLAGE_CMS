@echo off
echo ===============================================
echo  Altona Village CMS - Virtual Environment Fix
echo ===============================================
echo.
echo This script will:
echo 1. Remove the old virtual environment
echo 2. Create a new virtual environment
echo 3. Install all required packages
echo.
pause

echo.
echo Step 1: Removing old virtual environment...
if exist .venv (
    rmdir /s /q .venv
    echo ✅ Old virtual environment removed
) else (
    echo ℹ️  No existing virtual environment found
)

echo.
echo Step 2: Creating new virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    echo 💡 Make sure Python is installed and in your PATH
    pause
    exit /b 1
)
echo ✅ New virtual environment created

echo.
echo Step 3: Activating virtual environment...
call .venv\Scripts\activate.bat
echo ✅ Virtual environment activated

echo.
echo Step 4: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 5: Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install requirements
    echo 💡 Check that requirements.txt exists in the altona_village_cms directory
    pause
    exit /b 1
)

echo.
echo Step 6: Installing pandas and openpyxl for ERF address mapping...
pip install pandas openpyxl
if %errorlevel% neq 0 (
    echo ❌ Failed to install pandas and openpyxl
    pause
    exit /b 1
)

echo.
echo ===============================================
echo ✅ Virtual Environment Setup Complete!
echo ===============================================
echo.
echo Now you can:
echo 1. Start the backend: .venv\Scripts\python altona_village_cms\src\main.py
echo 2. Or use VS Code tasks to start both servers
echo.
echo Admin Login:
echo Email: vonlandsbergjohn@gmail.com
echo Password: dGdFHLCJxx44ykq
echo.
pause
