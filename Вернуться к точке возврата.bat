@echo off
title W3EE - restore snapshot

tasklist /FI "IMAGENAME eq witcher3.exe" 2>nul | find /I "witcher3.exe" >nul
if not errorlevel 1 (
    echo.
    echo   The Witcher 3 is still RUNNING.
    echo   Close the game completely, then run this file again.
    echo.
    pause
    exit /b 1
)

py -3 "%~dp0snapshot.py" --restore
echo.
pause
