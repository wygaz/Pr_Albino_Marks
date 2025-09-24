REM remote_s3.BAT
@echo off
cd /d "%~dp0"

set ENV_NAME=remote_s3
"%~dp0venv\Scripts\python.exe" manage.py check || goto :eof
REM >>> Só rode migrate manualmente se tiver CERTEZA de que quer alterar o DB remoto <<<
REM "%~dp0venv\Scripts\python.exe" manage.py migrate || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py runserver
