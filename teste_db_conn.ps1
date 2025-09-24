$env:ENV_NAME = "remote_s3"

@'
import os, psycopg2, dj_database_url
import pralbinomarks.settings as s  # garante que o .env.<ENV_NAME> foi lido

# limpa quaisquer variáveis PG que possam interferir no libpq
for k in list(os.environ):
    if k.startswith("PG"):
        os.environ.pop(k, None)

cfg = dj_database_url.parse(s.DATABASE_URL, conn_max_age=600, ssl_require=s.DB_SSL_REQUIRE)

params = dict(
    dbname   = cfg["NAME"],
    user     = cfg["USER"],
    password = cfg["PASSWORD"],
    host     = cfg["HOST"],
    port     = cfg["PORT"],
)
if cfg.get("OPTIONS", {}).get("sslmode") == "require":
    params["sslmode"] = "require"

print("Conectando com:", {k: params[k] for k in ("dbname","user","host","port","sslmode") if k in params})
conn = psycopg2.connect(**params)
with conn, conn.cursor() as cur:
    cur.execute("select version()")
    print("OK:", cur.fetchone()[0])
conn.close()
'@ | python -
