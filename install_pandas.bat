@echo off
echo Installing pandas and openpyxl for ERF address mapping functionality...
echo.

REM Activate virtual environment and install packages
.venv\Scripts\activate.bat && pip install pandas openpyxl

echo.
echo Installation complete!
echo Pandas is required for CSV/Excel file processing in the ERF address mapping system.
pause
