@echo off
title W3EE - migrate fork to original

tasklist /FI "IMAGENAME eq witcher3.exe" 2>nul | find /I "witcher3.exe" >nul
if not errorlevel 1 (
    echo.
    echo   The Witcher 3 is still RUNNING.
    echo   Close the game completely, then run this file again.
    echo.
    pause
    exit /b 1
)

py -3 "%~dp0migrate.py"
if errorlevel 1 goto :bad
echo.
echo   DONE. See the notes above.
goto :end

:bad
echo.
echo   SOMETHING WENT WRONG - read the messages above.

:end
echo.
pause
