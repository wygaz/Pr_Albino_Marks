# A_Lei_no_NT/admin.py
import re

from django.contrib import admin, messages
from django.db import transaction

from . import mensagens
from .forms import ArtigoForm
from .models import Artigo, Area, Autor


PAT_ALBINO = re.compile(r"\balbino\s+marks\b", re.IGNORECASE)


def _normalize(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")


def _first_line(html: str) -> str:
    s = _normalize(html)
    lines = s.split("\n")
    return (lines[0] if lines else "").strip()


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]*>", "", s)
    s = s.replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _should_fix(html: str) -> bool:
    first = _first_line(html)
    if not first:
        return False
    first_txt = _strip_tags(first)
    return bool(PAT_ALBINO.search(first_txt))


def _remove_first_line(html: str) -> str:
    s = _normalize(html)
    lines = s.split("\n")
    if len(lines) <= 1:
        return ""
    new = "\n".join(lines[1:])
    return new.lstrip("\n")


@admin.action(description="(DRY) Ver quantos têm 'Albino Marks' na 1ª linha do conteudo_html")
def dry_contar_albino_marks_primeira_linha(modeladmin, request, queryset):
    total = 0
    exemplos = []

    for obj in queryset.iterator():
        html = getattr(obj, "conteudo_html", "") or ""
        if _should_fix(html):
            total += 1
            if len(exemplos) < 8:
                exemplos.append(f"pk={obj.pk}: {_first_line(html)!r}")

    if total == 0:
        messages.info(request, "Nenhum registro do conjunto selecionado precisa de ajuste.")
        return

    msg = f"Encontrados {total} registro(s) com 'Albino Marks' na 1ª linha."
    if exemplos:
        msg += " Exemplos: " + " | ".join(exemplos)
    messages.warning(request, msg)


@admin.action(description="APLICAR: remover a 1ª linha quando ela contém 'Albino Marks' (conteudo_html)")
def aplicar_remover_primeira_linha_albino_marks(modeladmin, request, queryset):
    if not request.user.is_superuser:
        messages.error(request, "Ação bloqueada: apenas superusuário pode executar esta limpeza.")
        return

    updated_pks = []
    checked = 0

    with transaction.atomic():
        for obj in queryset.iterator():
            checked += 1
            html = getattr(obj, "conteudo_html", "") or ""
            if not _should_fix(html):
                continue
            new_html = _remove_first_line(html)
            if new_html != html:
                obj.conteudo_html = new_html
                obj.save(update_fields=["conteudo_html"])
                updated_pks.append(obj.pk)

    if not updated_pks:
        messages.info(request, f"Nenhuma alteração necessária. Verificados {checked} registro(s).")
        return

    # Evita estourar o tamanho da mensagem do admin
    MAX_PKS_MSG = 40
    preview = ", ".join(map(str, updated_pks[:MAX_PKS_MSG]))
    extra = ""
    if len(updated_pks) > MAX_PKS_MSG:
        extra = f" ... (+{len(updated_pks) - MAX_PKS_MSG} pk(s))"

    messages.success(
        request,
        f"Concluído. Verificados {checked}. Alterados {len(updated_pks)}. PKs: {preview}{extra}"
    )

    # Lista completa vai para o terminal/log do servidor
    print(f"[AdminAction] PKs alterados ({len(updated_pks)}): {updated_pks}")



@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    form = ArtigoForm

    # ⚠️ Se seu model NÃO tiver 'area' e/ou 'views', remova do list_display
    list_display = ("titulo", "ordem", "autor", "area", "visivel", "publicado_em", "views")
    list_display_links = ("titulo",)

    list_filter = ("area", "autor", "visivel")
    search_fields = ("titulo", "slug", "autor__nome", "area__nome")
    ordering = ("ordem", "-publicado_em")

    readonly_fields = ("slug", "views")
    list_editable = ("ordem", "visivel")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        mensagens.informar_titulo_ajustado(request, obj.titulo)
        mensagens.sucesso_artigo_salvo(request)

        if not obj.visivel:
            mensagens.aviso_artigo_oculto(request)

    actions = [
        dry_contar_albino_marks_primeira_linha,
        aplicar_remover_primeira_linha_albino_marks,
    ]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)
    ordering = ("nome",)
