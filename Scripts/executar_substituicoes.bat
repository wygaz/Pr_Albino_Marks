C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\apagar_artigos.bat"@echo off
REM =============================================
REM ATALHO PARA EXECUTAR O UTILITÁRIO DE SUBSTITUIÇÃO
REM =============================================

set SCRIPT_PATH="C:\Users\Wanderley\Apps\Utilitarios\Scripts\substituir_referencias.py"
set PROJETO_PATH="C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado"

echo Executando substituicoes no projeto:
echo %PROJETO_PATH%
echo.

python %SCRIPT_PATH% %PROJETO_PATH%

pause
