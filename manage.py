#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# Carrega .env apenas em ambiente local (se existir o arquivo)
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except Exception:
        # Se python-dotenv não estiver instalado, apenas segue sem erro
        pass
# Não imprimir credenciais/URLs em produção
# print("✔ DATABASE_URL =", os.getenv("DATABASE_URL"))

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
