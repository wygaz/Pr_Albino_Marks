import os
from pathlib import Path
from decouple import config
import dj_database_url

'''
# Verificar o valor diretamente do ambiente
try:
    print("Carregando variável DATABASE_URL...")
    print(f"Valor inicial: {os.environ.get('DATABASE_URL')}")
except Exception as e:
    print(f"Erro ao acessar DATABASE_URL: {e}")

# print("Variáveis de ambiente disponíveis:", dict(os.environ))

# Verificar o valor processado via config
db_url_via_config = config('DATABASE_URL', default='Fallback usado')
print(f"Valor da DATABASE_URL via config: {db_url_via_config}")
=======================================================================================
Checklist para Produção
Certifique-se de que DEBUG = False no arquivo settings.py.
Execute python manage.py collectstatic para reunir todos os arquivos estáticos em STATIC_ROOT.
Verifique se MEDIA_ROOT e MEDIA_URL estão configurados corretamente.
Configure o servidor web (Nginx/Apache) para servir arquivos de STATIC_ROOT e MEDIA_ROOT.
'''

if config('DEBUG', default=True, cast=bool):  # Exibe informações apenas se DEBUG=True
    raw_database_url = os.environ.get('DATABASE_URL', 'Não configurado')
  #  print(f"Valor bruto do DEBUG: {DEBUG}")
    print(f"Valor bruto da DATABASE_URL: {raw_database_url}")

    print("Carregando .env do caminho:", os.getcwd())  # Mostra o diretório atual
    print("DATABASE_URL:", config('DATABASE_URL', default="Não encontrado"))

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
#atribuindo nome à variável de ambiente DATABASE_NAME
print(f"DATABASE_NAME={config('DATABASE_NAME', default='railway')}")

# Carregar o ambiente
ENV = config('DJANGO_ENV', default='development')

if ENV == 'production':
    # Configurações de produção
    SECRET_KEY = config('SECRET_KEY', default='sua-chave-padrao-secreta-para-postgreSQL')
    DEBUG = config('DEBUG', default=False, cast=bool)
    ALLOWED_HOSTS = ['pr_albino_marks.up.railway.app', '127.0.0.1', 'localhost']

else:
    # Configurações de desenvolvimento
    SECRET_KEY = config('SECRET_KEY', default='sua-chave-padrao-secreta-para-dev')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
    

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'A_Lei_no_NT', 'templates', 'A_Lei_no_NT')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Arquivos de mídia (uploads de usuário, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

X_FRAME_OPTIONS = 'SAMEORIGIN'

# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'A_Lei_no_NT',  # Adicione seu aplicativo aqui
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL da aplicação
ROOT_URLCONF = 'Albino_Marks.urls'

# Banco de dados
#remoto (senha em variável de ambiente)


DATABASES = {
    'default': dj_database_url.config(default=config('DATABASE_URL'))  # Use a variável DATABASE_URL do ambiente Railway
}

'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
    }
}
'''

# Adicionar debug temporário
print(f"DATABASE_NAME={config('DATABASE_NAME')}")
print(f"DATABASE_USER={config('DATABASE_USER')}")
print(f"DATABASE_PASSWORD={config('DATABASE_PASSWORD')}")
print(f"DATABASE_HOST={config('DATABASE_HOST')}")
print(f"DATABASE_PORT={config('DATABASE_PORT')}")

# Validadores de senhas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Arquivos estáticos (CSS, JavaScript, Imagens)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'A_Lei_no_NT', 'static'),
]

# Configurações de segurança (adapte conforme necessário)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER')
ADMIN_EMAIL = os.environ.get('EMAIL_HOST_USER')

# Configurações de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'CRITICAL',
        },
        'A_Lei_no_NT': {  # Certifique-se de que seu módulo está configurado corretamente
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
}

#forçando deploy completo