import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import urllib.parse as _up

BASE_DIR = Path(__file__).resolve().parent.parent

# Detecta se estamos rodando o servidor DEV do Django (runserver / runserver_plus)
IS_RUNSERVER = any(cmd in sys.argv for cmd in ("runserver", "runserver_plus"))

# =========================================================
# 1) Carrega .env por perfil (ex.: .env.local / .env.remoto)
# =========================================================
ENV_NAME = os.getenv("ENV_NAME", "local").strip().lower()
env_file = BASE_DIR / f".env.{ENV_NAME}"
if env_file.exists():
    load_dotenv(env_file, override=True)  # ✅ o .env do perfil sempre vence

# =========================================================
# 2) Configurações básicas (dependem do env)
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes")
LOGIN_REDIRECT_URL = "/admin/"

RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
USE_RAILWAY_DOMAIN = os.getenv("USE_RAILWAY_DOMAIN", "0").strip().lower() in ("1", "true", "yes")

# Atrás de proxy HTTPS (Cloudflare/Railway)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================================
# 3) Hosts / CSRF
# =========================================================
ALLOWED_HOSTS = [
    "albinomarks.com.br",
    "www.albinomarks.com.br",
    "127.0.0.1",
    "localhost",
    ".railway.app",
    ".up.railway.app",
]
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

# Em DEV (runserver) permitir HTTP local, mesmo que DEBUG=0 (perfil remoto)
if IS_RUNSERVER or DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://127.0.0.1:8000",   # útil se você usar runserver_plus
        "https://localhost:8000",
    ]

# =========================================================
# 4) Cookies / SSL
#    REGRA DE OURO: runserver NUNCA deve forçar HTTPS
# =========================================================
if IS_RUNSERVER or DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
else:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"

    if USE_RAILWAY_DOMAIN:
        SESSION_COOKIE_DOMAIN = None
        CSRF_COOKIE_DOMAIN = None
    else:
        SESSION_COOKIE_DOMAIN = ".albinomarks.com.br"
        CSRF_COOKIE_DOMAIN = ".albinomarks.com.br"

    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0") or 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

# =========================================================
# 5) Banco (DATABASE_URL preferida; fallback DATABASE_PUBLIC_URL)
# =========================================================
_db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not _db_url:
    raise RuntimeError("DATABASE_URL não definido. Defina no .env.local/.env.remoto ou nas variables do Railway.")

DB_SSL_REQUIRE = os.getenv("DB_SSL_REQUIRE", "1").strip().lower() in ("1", "true", "yes")
DATABASES = {
    "default": dj_database_url.parse(
        _db_url,
        conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "600")),
        ssl_require=DB_SSL_REQUIRE,
    )
}

# =========================================================
# 6) Banner mínimo no runserver (Projeto + host do BD)
# =========================================================
def _should_print_banner() -> bool:
    return IS_RUNSERVER and (os.environ.get("RUN_MAIN") == "true" or "--noreload" in sys.argv)

def _db_host(url: str) -> str:
    try:
        return _up.urlparse(url).hostname or "?"
    except Exception:
        return "?"

if _should_print_banner():
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Pr_Albino_Marks")
    host = _db_host(_db_url)
    origem = "LOCAL" if host in ("localhost", "127.0.0.1") else ("RAILWAY" if ("rlwy" in host or "railway" in host) else "OUTRO")
    print(f"\n🚦 {PROJECT_NAME} | BD: {origem} | host={host} | ENV_NAME={ENV_NAME}\n")

# ========= Apps =========
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "A_Lei_no_NT",
    "pralbinomarks",

    # útil em dev para WhiteNoise assumir o controle
    "whitenoise.runserver_nostatic",
]

if DEBUG and "django_extensions" not in INSTALLED_APPS:
    INSTALLED_APPS.append("django_extensions")

# ========= Middleware =========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
            BASE_DIR / "templates",
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
USE_TZ = True

# ========= Static =========
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# 🔥 CRÍTICO: em dev (runserver/runserver_plus) NÃO use Manifest
# (evita "Missing staticfiles manifest entry")
if IS_RUNSERVER or DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ========= Media / Storage =========
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Ativa uso de S3 se USE_S3=1 (ou USE_S3_FOR_MEDIA=1) estiver definido no ambiente
USE_S3 = os.getenv("USE_S3", os.getenv("USE_S3_FOR_MEDIA", "0")).strip() == "1"

if USE_S3:
    if "storages" not in INSTALLED_APPS:
        INSTALLED_APPS.append("storages")

    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_STORAGE_BUCKET_NAME")

    AWS_S3_REGION_NAME = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_S3_REGION_NAME", "us-east-1"))
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")  # opcional
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

    # URLs assinadas (bucket privado)
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = int(os.getenv("AWS_QUERYSTRING_EXPIRE", "86400"))  # 24h

    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=31536000, public"}

    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")  # ex: dxxxx.cloudfront.net
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    else:
        # ajuste se você usa endpoint customizado; senão S3 padrão:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

# ========= Default Auto Field =========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========= Pastas de PDF =========
PDF_OUTPUT_DIR  = BASE_DIR / "media" / "pdfs"
PDF_ARTIGOS_DIR = PDF_OUTPUT_DIR / "artigos"

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


