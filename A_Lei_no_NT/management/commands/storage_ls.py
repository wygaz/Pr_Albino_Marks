from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage


class Command(BaseCommand):
    help = "Lista arquivos/pastas no default_storage (filesystem ou S3), a partir de um prefixo."

    def add_arguments(self, parser):
        parser.add_argument("--prefix", default="", help="Ex: imagens/artigos")
        parser.add_argument("--recursive", action="store_true", help="Listar recursivamente")
        parser.add_argument("--contains", default="", help="Filtrar por substring (case-insensitive)")
        parser.add_argument("--show-url", action="store_true", help="Tentar imprimir URL do arquivo")

    def handle(self, *args, **opts):
        prefix = (opts["prefix"] or "").strip().strip("/")
        contains = (opts["contains"] or "").strip().lower()
        recursive = bool(opts["recursive"])
        show_url = bool(opts["show_url"])

        def walk(p):
            dirs, files = default_storage.listdir(p)
            for f in sorted(files):
                rel = f"{p}/{f}".strip("/")
                if contains and contains not in rel.lower():
                    continue
                line = rel
                if show_url:
                    try:
                        line += "  " + default_storage.url(rel)
                    except Exception:
                        pass
                self.stdout.write(line)

            if recursive:
                for d in sorted(dirs):
                    walk(f"{p}/{d}".strip("/"))

        walk(prefix)
