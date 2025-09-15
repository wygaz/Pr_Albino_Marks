from A_Lei_no_NT import utils
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils.text import slugify

from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT import utils

class Command(BaseCommand):
    help = (
        "Audita consistência de Artigos: título/slug, DOCX (media/uploads/<slug>.docx), "
        "capa (media/imagens/artigos/<slug>.*) e PDF (static/pdfs/<slug>.pdf). "
        "Use --fix para corrigir automaticamente nomes e caminhos (DOCX + capa)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--clean", action="store_true",
                            help="Além do --fix, move legados e duplicados para quarentena segura.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Mostra o que seria feito sem alterar nada.")
        parser.add_argument("--fix", action="store_true",
                            help="Aplica correções (renomeia/move arquivos e ajusta campos no BD).")
        parser.add_argument("--ordem", default="id",
                            help="Campo para ordenar artigos na listagem (padrão: id).")

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        do_fix = opts["fix"]
        do_clean = opts["clean"]

        order = opts["ordem"]

        base_dir = Path(settings.BASE_DIR)
        static_pdfs = (base_dir / "static" / "pdfs")  # servidos pelo WhiteNoise
        total = ok = pend_pdf = pend_docx = pend_capa = 0

        artigos = Artigo.objects.all().order_by(order)
        self.stdout.write(self.style.NOTICE(f"Verificando {artigos.count()} artigos…\n"))

        for a in artigos:
            total += 1
            titulo_base = utils.limpar_numeracao(a.titulo or "")
            slug_alvo = slugify(a.slug or slugify(titulo_base))[:90]  # mantém slug se já houver
            head = f"[{a.id}] slug='{a.slug}' base='{titulo_base}'"


            # --- DOCX: localizar no padrão novo ou legado ---
            docx_target = utils.path_docx_por_slug(slug_alvo)
            docx_encontrado = utils.localizar_docx(slug_alvo)
            falta_docx = docx_encontrado is None

            if falta_docx:
                pend_docx += 1
                self.stdout.write(self.style.WARNING(
                    f"{head}  ⚠ DOCX ausente -> {docx_target.relative_to(settings.MEDIA_ROOT)}"
                ))
            else:
                # Se achou em local/nomes legados, com --fix normaliza para o alvo
                if do_fix and not dry and docx_encontrado != docx_target:
                    novo = utils.normalizar_docx_para_padrao(slug_alvo, docx_encontrado)
                    a.arquivo_word.name = str(novo.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
                    a.save(update_fields=["arquivo_word"])
                    self.stdout.write(self.style.SUCCESS(f"    DOCX normalizado -> {a.arquivo_word.name}"))


                # CAPA
                # --- CAPA ---
                capa_target = utils.encontrar_capa_existente(slug_alvo)
                falta_capa = capa_target is None

                if falta_capa:
                    pend_capa += 1
                    self.stdout.write(self.style.WARNING(
                        f"{head}  ⚠ Capa ausente -> imagens/artigos/<slug>.(jpg|png)"
                    ))
                else:
                    if do_fix and not dry and getattr(a, "imagem_capa", None):
                        # Atualiza o campo no BD para apontar para o caminho correto
                        rel = str(capa_target.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
                        if a.imagem_capa.name != rel:
                            a.imagem_capa.name = rel
                            a.save(update_fields=["imagem_capa"])
                            self.stdout.write(self.style.SUCCESS(f"    Capa normalizada -> {a.imagem_capa.name}"))


        # Resumo
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumo"))
        self.stdout.write(f"Total: {total} | OK: {ok}")
        self.stdout.write(f"Pendências: DOCX={pend_docx}  Capa={pend_capa}  PDF={pend_pdf}")
        self.stdout.write(self.style.NOTICE(f"Dry-run: {dry} | Fix aplicado: {do_fix and not dry}"))
