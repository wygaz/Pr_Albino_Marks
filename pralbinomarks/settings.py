import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

# Configurações de segurança
import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes")

# Detecta subdomínio público da Railway, se existir (ex.: 5nc3lj5a.up.railway.app)
RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()  # Railway injeta isso em prod
USE_RAILWAY_DOMAIN   = os.getenv("USE_RAILWAY_DOMAIN", "0").strip().lower() in ("1", "true", "yes")

# Atrás de proxy HTTPS (Cloudflare/Railway)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ===== Hosts / CSRF =====
ALLOWED_HOSTS = [
    "albinomarks.com.br",
    "www.albinomarks.com.br",
]

# Inclui o domínio público da Railway (útil para healthcheck e testes em prod)
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    "https://albinomarks.com.br",
    "https://www.albinomarks.com.br",
    "https://*.railway.app",
    "https://*.up.railway.app",
]
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

# Se estiver em desenvolvimento local (DEBUG=1), permita localhost/127.0.0.1 em HTTP
if DEBUG:
    ALLOWED_HOSTS += ["127.0.0.1", "localhost"]
    CSRF_TRUSTED_ORIGINS += [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

# ===== Cookies / SSL =====
if DEBUG:
    # Ambiente local: HTTP
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
else:
    # Produção: HTTPS e cookies seguros
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"

    # Se o site público usa seu domínio, fixe o domínio do cookie; se só Railway, deixe None
    if USE_RAILWAY_DOMAIN:
        SESSION_COOKIE_DOMAIN = None
        CSRF_COOKIE_DOMAIN = None
    else:
        SESSION_COOKIE_DOMAIN = ".albinomarks.com.br"
        CSRF_COOKIE_DOMAIN = ".albinomarks.com.br"

    # HSTS (opcional, controlado por env)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0") or 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

LOGIN_REDIRECT_URL = "/admin/"


BASE_DIR = Path(__file__).resolve().parent.parent

# ENV_NAME escolhe qual .env carregar *se* existir (local/remote/prod)
ENV_NAME = os.getenv("ENV_NAME", "local")
env_file = BASE_DIR / f".env.{ENV_NAME}"
if env_file.exists():
    load_dotenv(env_file)  # local: carrega do arquivo

# Escolhe a URL do banco por prioridade:
    # 1) DATABASE_URL (sempre preferida)
    # 2) DATABASE_PUBLIC_URL (fallback para acesso externo quando estiver rodando local)
_db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")

if not _db_url:
    raise RuntimeError(
        "DATABASE_URL não definido. "
        "Defina DATABASE_URL (produção/contêiner) ou use o valor de DATABASE_PUBLIC_URL quando for acessar remotamente a partir do Django local."
    )

# Railway/Postgres normalmente requer SSL (obrigatório fora de redes 100% locais)
DB_SSL_REQUIRE = os.getenv("DB_SSL_REQUIRE", "1").strip().lower() in ("1", "true", "yes")

DATABASES = {
    "default": dj_database_url.parse(
        _db_url,
        conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "600")),
        ssl_require=DB_SSL_REQUIRE,
    )
}

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".railway.app",
    "www.albinomarks.com.br",
    "albinomarks.com.br", 
    "pralbinomarks-production.up.railway.app",
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
# Ativa uso de S3 se USE_S3=1 (ou USE_S3_FOR_MEDIA=1) estiver definido no ambiente
USE_S3 = os.getenv("USE_S3", os.getenv("USE_S3_FOR_MEDIA", "0")).strip() == "1"

if USE_S3:
    INSTALLED_APPS += ["storages"]

    # Backend de armazenamento padrão para arquivos de mídia
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # Credenciais e parâmetros base
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = (
        os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_STORAGE_BUCKET_NAME")
    )

    # Região e endpoint (Wasabi / Backblaze / etc. usam endpoint próprio)
    AWS_S3_REGION_NAME = os.getenv(
        "AWS_DEFAULT_REGION", os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    )
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")  # opcional
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    # Comportamento e permissões
    AWS_S3_FILE_OVERWRITE = False  # não sobrescreve uploads
    AWS_DEFAULT_ACL = None         # ACL neutra, usa permissões IAM

    # URLs assinadas → impedem AccessDenied sem precisar deixar o bucket público
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = int(os.getenv("AWS_QUERYSTRING_EXPIRE", "86400"))  # 24h

    # Cache dos objetos de mídia (imagens, PDFs, DOCX)
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=31536000, public"  # 1 ano
    }

    # Domínio do bucket (ou CDN)
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")  # ex: dxxxx.cloudfront.net
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    else:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

    # Não define MEDIA_ROOT quando usa S3
else:
    # Storage local (ambiente de desenvolvimento)
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"


# Pastas de PDF sempre válidas (independente do ramo acima)
PDF_OUTPUT_DIR  = BASE_DIR / "media" / "pdfs"
PDF_ARTIGOS_DIR = PDF_OUTPUT_DIR / "artigos"


# settings.py (adicione no final)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "INFO"},
        "django.contrib.auth": {"handlers": ["console"], "level": "DEBUG"},
    },
}

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]


'''
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
'''








