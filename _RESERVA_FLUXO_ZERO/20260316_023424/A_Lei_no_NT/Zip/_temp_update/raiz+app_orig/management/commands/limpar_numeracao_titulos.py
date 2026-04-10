import re

from django.core.management.base import BaseCommand
from A_Lei_no_NT.models import Artigo

# casa coisas do tipo: " (1 de 2)" no final do título
PADRAO_NUM = re.compile(r"\s*\(\s*\d+\s+de\s+\d+\s*\)\s*$", re.IGNORECASE)


class Command(BaseCommand):
    help = (
        "Remove o sufixo '(X de Y)' dos títulos dos artigos "
        "e deixa o modelo recalcular slug/arquivos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Grava as alterações. Sem esta flag é só dry-run (apenas mostra).",
        )

    def handle(self, *args, **options):
        aplicar = options["aplicar"]
        artigos = Artigo.objects.all().order_by("id")

        total = artigos.count()
        alterados = 0
        self.stdout.write(f"{total} artigos encontrados.\n")

        for art in artigos:
            titulo_antigo = (art.titulo or "").strip()
            if not titulo_antigo:
                continue

            # só mexe se tiver "(X de Y)" no final
            if not PADRAO_NUM.search(titulo_antigo):
                continue

            titulo_novo = PADRAO_NUM.sub("", titulo_antigo).strip()

            self.stdout.write(f"ID {art.id}:")
            self.stdout.write(f"  título : {titulo_antigo!r} -> {titulo_novo!r}")
            self.stdout.write(f"  slug   : {art.slug!r}  (será recalculado pelo save)\n")

            if aplicar:
                # mudar o título e deixar o save() fazer:
                # - slug novo (porque o título mudou)
                # - renome de DOCX, PDF, capa, conforme já está no modelo
                art.titulo = titulo_novo
                art.save()  # aqui dispara toda a lógica que já existe
                alterados += 1

        if aplicar:
            self.stdout.write(self.style.SUCCESS(
                f"Concluído. {alterados} artigos tiveram o título limpo."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "Dry-run: nenhuma alteração foi gravada.\n"
                "Revise a saída acima. Quando estiver seguro, "
                "rode novamente com `--aplicar`."
            ))
