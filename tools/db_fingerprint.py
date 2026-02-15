from django.conf import settings
from django.db import connection
from django.apps import apps

print("HOST=", settings.DATABASES["default"].get("HOST"))
print("NAME=", settings.DATABASES["default"].get("NAME"))

with connection.cursor() as cur:
    cur.execute("select current_database(), version()")
    print("DB_FINGERPRINT=", cur.fetchone())

    cur.execute("select count(*) from django_migrations")
    print("MIGRATIONS_ROWS=", cur.fetchone()[0])

Artigo = apps.get_model("A_Lei_no_NT", "Artigo")
print("ARTIGOS=", Artigo.objects.count())
