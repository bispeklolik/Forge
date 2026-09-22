@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================
echo  W3EE tweaks - REVERT (restore from backup)
echo ============================================
echo.
echo  Every patched file is restored from its
echo  .orig_w3ee_tweaks backup. All steps at once
echo  - a backup holds the whole pristine file.
echo.
echo  Close The Witcher 3 before continuing.
echo.
pause

set PY=py -3
%PY% --version >nul 2>&1
if errorlevel 1 set PY=python
%PY% --version >nul 2>&1
if errorlevel 1 goto nopython

echo.
%PY% apply.py --revert
echo.
goto done

:nopython
echo.
echo ERROR: Python 3 not found.
echo Install Python 3 from python.org and run this again.
echo.

:done
pause
