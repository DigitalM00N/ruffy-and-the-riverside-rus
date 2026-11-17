@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Окружение не найдено — сначала запускался install.bat?
  pause & exit /b 1
)
".venv\Scripts\python.exe" -I tools\install.py --uninstall %*
pause
