REM Utiliza o Banco de Dados local

@echo off
REM Vai para a pasta onde este .bat está salvo (raiz do projeto)
cd /d "%~dp0"

set ENV_NAME=local
"%~dp0venv\Scripts\python.exe" manage.py check || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py migrate || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py runserver
