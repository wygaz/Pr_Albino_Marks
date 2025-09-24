REM Esses .bat só escolhem qual .env.[ENV_NAME] carregar no ambiente local.
REM No Railway, você não usa .bat: lá você define as variáveis no painel, e o deploy roda com elas.

REM No painel do Railway, em Variables, crie:
REM ENV_NAME = prod (opcional, para consistência)
REM    DATABASE_URL (do Postgres de produção)
REM    DB_SSL_REQUIRE = 1 (se necessário)
REM    DEBUG = 0
REM    Se S3: 
REM      USE_S3=1, AWS_*…
REM 
REM Dessa forma, o Railway vai utilizar o que estiver em DATABASE_URL do Railway

@echo off
cd /d "%~dp0"

set ENV_NAME=prod
"%~dp0venv\Scripts\python.exe" manage.py check || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py collectstatic --noinput || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py migrate || goto :eof
"%~dp0venv\Scripts\python.exe" manage.py runserver
