@echo off
REM Altona Village CMS - Quick Backup Script
REM Run this to create a complete backup quickly

echo.
echo ========================================
echo ALTONA VILLAGE CMS - QUICK BACKUP
echo ========================================
echo.

cd /d "%~dp0"

echo Creating complete backup...
python complete_backup_system.py

echo.
echo Backup process completed!
echo Check the BACKUPS folder for your backup files.
echo.
pause
