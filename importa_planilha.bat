@echo off
cd /d C:\Users\Wanderley\Apps\Utilitarios\Scripts
call ..\..\Pr_Albino_Marks_restaurado\venv\Scripts\activate
python importar_planilha_para_banco.py
pause