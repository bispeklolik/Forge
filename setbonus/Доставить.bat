@echo off
chcp 65001 >nul
title Доставить мод рун в игру
cd /d "%~dp0"

tasklist /FI "IMAGENAME eq witcher3.exe" | find /I "witcher3.exe" >nul
if not errorlevel 1 (
  echo.
  echo   Игра ещё запущена. Закройте её и запустите этот файл снова.
  echo.
  pause
  exit /b 1
)

echo.
echo   === 1/5  Скрипт мода ===
python build_core.py
if errorlevel 1 goto oops

echo.
echo   === 2/5  Предметы и подписи ===
python build_item.py
if errorlevel 1 goto oops

echo.
echo   === 3/5  Раздел настроек ===
python build_menu.py
if errorlevel 1 goto oops

echo.
echo   === 4/5  Упаковка предметов в дополнение ===
python build_dlc.py
if errorlevel 1 goto oops

echo.
echo   === 5/5  Реликтовые комплекты ===
python build_relics.py
if errorlevel 1 goto oops

echo.
echo   Готово. Можно запускать игру.
pause
exit /b 0

:oops
echo.
echo   Что-то пошло не так — покажите этот текст Клоду.
pause
exit /b 1
