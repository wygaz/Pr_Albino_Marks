@echo off
echo Iniciando o servidor Django com HTTPS (runserver_plus)...

REM Ativar ambiente virtual
call venv\Scripts\activate

REM Rodar o servidor com runserver_plus em https://localhost:8000/
python manage.py runserver_plus --cert-file=localhost.crt --key-file=localhost.key localhost:8000
REM python manage.py runserver_plus --cert-file=certificado.pem --key-file=chave-privada.pem 0.0.0.0:8000

pause
