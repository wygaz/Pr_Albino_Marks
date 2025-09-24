REM remote.bat (rodar na sua máquina, conectando ao Postgres remoto)

@echo off
cd /d "%~dp0"

set ENV_NAME=remote
"%~dp0venv\Scripts\python.exe" manage.py check || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py migrate || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py runserver
