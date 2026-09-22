@echo off
tasklist /FI "IMAGENAME eq witcher3.exe" | find /I "witcher3.exe" >nul
if not errorlevel 1 (
  echo The game is still running. Close it first, then run this again.
  pause
  exit /b 1
)
xcopy /Y /Q "C:\Users\New\AppData\Local\Temp\sbt_stage\*" "F:\SteamLibrary\steamapps\common\The Witcher 3\mods\modSetBonusTransfer\content\" >nul
echo Runestones installed. Start the game.
pause
