import os
from pathlib import Path
import environ
import dj_database_url  # ok manter se usar DATABASE_URL

BASE_DIR = Path(__file__).resolve().parent.parent

# ========= .env =========
env = environ.Env()
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    env.read_env(str(ENV_FILE))

DEBUG = env.bool("DEBUG", default=(os.getenv("RAILWAY_ENVIRONMENT") is None))
SECRET_KEY = env("SECRET_KEY", default="dev-secret")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".railway.app", "albino....com.br"]  # seu domínio

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
    "django_extensions",  # opcional (dev)
    "whitenoise.runserver_nostatic",  # dev: desliga static do runserver
    "django.contrib.staticfiles",
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

# Usa DATABASE_URL quando houver (local ou Railway)
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,                      # pool
        ssl_require=bool(os.getenv("RAILWAY_ENVIRONMENT")),  # SSL só em produção
    )
}


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
    # Não defina MEDIA_URL aqui; o storage retorna .url nos FileField
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
