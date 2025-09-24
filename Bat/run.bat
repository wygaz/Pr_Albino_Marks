@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM --- OPCIONAL: limite os bat a um subdiretório (ex.: scripts\)
REM set "SEARCH_DIR=%~dp0scripts"
REM if not exist "%SEARCH_DIR%" set "SEARCH_DIR=%~dp0"
REM pushd "%SEARCH_DIR%"

echo.
echo ====== Selecione um .BAT para executar ======
echo.

set "i=0"
for %%F in (*.bat) do (
  if /I not "%%~nxF"=="run.bat" (
    set /a i+=1
    set "opt[!i!]=%%~nxF"
    echo   !i!. %%~nxF
  )
)

if %i%==0 (
  echo (nao ha .bat nesta pasta)
  pause
  exit /b
)

echo.
set /p CH=Digite o numero e pressione ENTER (ou vazio para sair): 
if "%CH%"=="" exit /b

REM valida numero
for /f "delims=0123456789" %%X in ("%CH%") do (
  echo Opcao invalida.
  exit /b 1
)
if %CH% LSS 1 if %CH% GTR %i% (
  echo Fora do intervalo.
  exit /b 1
)

set "SEL=!opt[%CH%]!"
echo.
echo Executando: %SEL%
echo ---------------------------
call "%SEL%"
endlocal
