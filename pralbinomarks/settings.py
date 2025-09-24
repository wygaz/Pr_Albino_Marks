import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ENV_NAME escolhe qual .env carregar *se* existir (local/remote/prod)
ENV_NAME = os.getenv("ENV_NAME", "local")
env_file = BASE_DIR / f".env.{ENV_NAME}"
if env_file.exists():
    load_dotenv(env_file)  # local: carrega do arquivo

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes")

# Banco (sempre Postgres via DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL não definido. Ajuste suas variáveis de ambiente.")

DB_SSL_REQUIRE = os.getenv("DB_SSL_REQUIRE", "0").strip().lower() in ("1", "true")
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=DB_SSL_REQUIRE,
    )
}


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".railway.app",
    "www.albinomarks.com.br",
    "albinomarks.com.br",
]

CSRF_TRUSTED_ORIGINS = [
    "https://albinomarks.com.br",
    "https://www.albinomarks.com.br",
]

# ========= Apps =========
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "A_Lei_no_NT",
    "pralbinomarks",      # ok se você realmente tem app/config dentro do pacote do projeto
    "whitenoise.runserver_nostatic",  # dev: desliga static do runserver
  ]

# ========= Middleware =========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # static em produção
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pralbinomarks.urls"

# ========= Templates =========
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",                               # (opcional) global
            BASE_DIR / "A_Lei_no_NT" / "templates" / "A_Lei_no_NT",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pralbinomarks.wsgi.application"

# ========= Password validation =========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========= I18N / TZ =========
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True  # (USE_L10N é deprecado; remova)

# static

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"          # pasta de coleta
STATICFILES_DIRS = [BASE_DIR / "static"]        # seus arquivos-fonte
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

if DEBUG:
    INSTALLED_APPS += ["django_extensions"]

# ========= Media / Storage =========
if os.getenv("USE_S3") == "1":
    INSTALLED_APPS += ["storages"]
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")  # opcional (Wasabi/B2)
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None

    # Se tiver CDN, descomente as 2 linhas abaixo:
    # AWS_S3_CUSTOM_DOMAIN = "cdn.seudominio.com"
    # MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# Pastas de PDF sempre válidas (independente do ramo acima)
PDF_OUTPUT_DIR  = BASE_DIR / "media" / "pdfs"
PDF_ARTIGOS_DIR = PDF_OUTPUT_DIR / "artigos"

# ========= CSRF =========
CSRF_TRUSTED_ORIGINS = [
    "https://www.albinomarks.com.br",
    "https://albinomarks.com.br",
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}

# ===== Segurança em produção =====
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0") or 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

