@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================
echo  W3EE tweaks - APPLY  (steps 1,2,3,4,5)
echo ============================================
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
echo --- Step 1: dry run (check only, nothing is written) ---
echo.
%PY% apply.py --dry-run --steps 1,2,3,4,5
if errorlevel 1 goto dryfailed

echo.
echo --------------------------------------------
echo  Dry run is clean. Press any key to APPLY,
echo  or close this window to cancel.
echo --------------------------------------------
pause

echo.
%PY% apply.py --steps 1,2,3,4,5
echo.
goto done

:dryfailed
echo.
echo ============================================
echo  DRY RUN REPORTED PROBLEMS - NOTHING APPLIED
echo ============================================
echo  See the lines marked OSHIBKA above.
echo  Usually this means W3EE was updated and the
echo  code changed. Read CHTO-ETO (the .md file).
echo.
goto done

:nopython
echo.
echo ERROR: Python 3 not found.
echo Install Python 3 from python.org and run this again.
echo.

:done
pause
