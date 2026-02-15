import os
import sys
from pathlib import Path

# garante que a RAIZ do projeto está no sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")
django.setup()

from django.conf import settings
from django.db import connection
from django.apps import apps


def one(sql: str):
    with connection.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()


print("ENV_NAME=", os.getenv("ENV_NAME"))
print("HOST=", settings.DATABASES["default"].get("HOST"))
print("NAME=", settings.DATABASES["default"].get("NAME"))
print("DB_FINGERPRINT=", one("select current_database(), version()"))

try:
    print("MIGRATIONS_ROWS=", one("select count(*) from django_migrations")[0])
except Exception as e:
    print("MIGRATIONS_ROWS=ERROR", repr(e))

try:
    Artigo = apps.get_model("A_Lei_no_NT", "Artigo")
    print("ARTIGOS=", Artigo.objects.count())
except Exception as e:
    print("ARTIGOS=ERROR", repr(e))
