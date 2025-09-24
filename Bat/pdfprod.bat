@echo off
cd /d "%~dp0"
set ENV_NAME=remote_s3
"%~dp0venv\Scripts\python.exe" manage.py gerar_pdf_local_salvar_na_Producao --all
pause
