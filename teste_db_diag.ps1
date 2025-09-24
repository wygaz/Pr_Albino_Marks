$env:ENV_NAME = "remote_s3"

@'
import os
from pprint import pprint
import dj_database_url
import pralbinomarks.settings as s  # importa settings e carrega o .env.<ENV_NAME>

print("ENV_NAME:", os.getenv("ENV_NAME"))
print("DATABASE_URL (from settings):", s.DATABASE_URL)
print("DB_SSL_REQUIRE:", s.DB_SSL_REQUIRE)

cfg = dj_database_url.parse(s.DATABASE_URL, conn_max_age=600, ssl_require=s.DB_SSL_REQUIRE)
print("\nDjango DB dict (parse):")
pprint(cfg)

print("\nPG* env vars que existem:")
pg = {k:v for k,v in os.environ.items() if k.startswith("PG")}
pprint(pg)
'@ | python -
