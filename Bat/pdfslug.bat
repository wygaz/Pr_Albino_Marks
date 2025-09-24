@echo off
REM Gera o PDF de um artigo específico (informar slug)

set /p SLUG=Digite o slug do artigo: 
call venv\Scripts\activate
python manage.py gerar_pdfs_local --slug %SLUG%
pause
