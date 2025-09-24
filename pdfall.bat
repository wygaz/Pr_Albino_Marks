@echo off
REM Gera os PDFs de todos os artigos

call venv\Scripts\activate
python manage.py gerar_pdfs_local --all
pause
