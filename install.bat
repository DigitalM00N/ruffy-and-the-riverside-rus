@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul || (
  echo Нужен Python 3.10+ : https://www.python.org/downloads/  ^(при установке отметьте "Add python.exe to PATH"^)
  pause & exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Подготовка окружения...
  %PY% -m venv .venv || (pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || (pause & exit /b 1)
".venv\Scripts\python.exe" -I tools\install.py %*
pause
