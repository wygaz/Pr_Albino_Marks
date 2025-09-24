# tools/apply_storage_safe_refactor.py
"""
Refatoração segura para storage-agnostic (S3 compatível):
- Converte padrões 100% seguros:
    open(x.path, "rb") -> open_file(x, "rb")
    open(x.path, "wb") -> open_file(x, "wb")
    open(x.path, "r")  -> open_file(x, "r")
    open(x.path, "w")  -> open_file(x, "w")
- Insere import "from A_Lei_no_NT.utils_storage import open_file"
  (e "get_file_url" se usar o modo --replace-urls)
- Gera relatório de outros usos de ".path" para revisão manual.
- Ignora pastas típicas: venv, .venv, migrations, static, media, .git, __pycache__.

Uso:
  # Dry-run (só relata e mostra o que seria alterado)
  python tools/apply_storage_safe_refactor.py

  # Aplicar mudanças seguras (open(... .path ...))
  python tools/apply_storage_safe_refactor.py --apply

  # (Opcional) Também substituir usos simples de ".path" por get_file_url(...)
  # EX: f"{obj.arquivo.path}" -> f"{get_file_url(obj.arquivo)}"
  # Use com cautela e revise o diff depois:
  python tools/apply_storage_safe_refactor.py --apply --replace-urls
"""
import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # raiz do projeto
INCLUDE_EXT = {".py"}
SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "static", "media", "migrations"}

# Padrões seguros: open( <expr>.path , "rb"/"wb"/"r"/"w" [, ...])
RE_OPEN_PATH = re.compile(
    r"""open\(\s*([A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.path\s*,\s*(['"][rwb]{1,2}['"])""",
    re.MULTILINE,
)

# Usos genéricos de ".path" (para relatório / opção --replace-urls)
RE_ANY_PATH = re.compile(r"""([A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.path\b""")

# Para inserir import utilitário
IMPORT_LINE_OPEN = "from A_Lei_no_NT.utils_storage import open_file"
IMPORT_LINE_BOTH = "from A_Lei_no_NT.utils_storage import open_file, get_file_url"
IMPORT_LINE_GET = "from A_Lei_no_NT.utils_storage import get_file_url"

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(sd in parts for sd in SKIP_DIRS)

def ensure_import(lines: list[str], want_get: bool) -> list[str]:
    text = "\n".join(lines)
    has_open = "open_file" in text
    has_get = "get_file_url" in text
    if want_get:
        if not (has_open and has_get):
            # tenta inserir abaixo do primeiro import
            for i, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    lines.insert(i + 1, IMPORT_LINE_BOTH + "\n")
                    break
            else:
                lines.insert(0, IMPORT_LINE_BOTH + "\n")
    else:
        if not has_open:
            for i, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    lines.insert(i + 1, IMPORT_LINE_OPEN + "\n")
                    break
            else:
                lines.insert(0, IMPORT_LINE_OPEN + "\n")
        # se por acaso houver get_file_url no arquivo e não tem import dele, adiciona
        if has_get and "get_file_url" not in text.splitlines()[0]:
            # só insere se não inserimos BOTH acima
            if IMPORT_LINE_BOTH not in "\n".join(lines) and IMPORT_LINE_GET not in "\n".join(lines):
                for i, line in enumerate(lines):
                    if line.startswith("from ") or line.startswith("import "):
                        lines.insert(i + 1, IMPORT_LINE_GET + "\n")
                        break
                else:
                    lines.insert(0, IMPORT_LINE_GET + "\n")
    return lines

def replace_open_path(content: str) -> tuple[str, int]:
    """
    Substitui open(x.path, "rb") por open_file(x, "rb"), etc.
    Retorna (novo_conteudo, contagem_substituicoes)
    """
    def _repl(m: re.Match) -> str:
        expr = m.group(1)  # x ou obj.campo etc
        mode = m.group(2)  # "rb" | "wb" | "r" | "w"
        return f"open_file({expr}, {mode}"

    new = RE_OPEN_PATH.sub(_repl, content)
    count = len(list(RE_OPEN_PATH.finditer(content)))
    return new, count

def replace_path_with_get_url(content: str) -> tuple[str, int]:
    """
    Modo opcional: troca usos simples de ".path" por get_file_url(...)
    Evita tocar em chamadas 'open(' que já foram tratadas acima.
    """
    # Não substituir dentro de open( ... .path ... ) — já tratado
    tmp = content

    # Substitui x.path -> get_file_url(x) nos casos simples
    # (regex ingênuo; revise o diff após aplicar)
    def _repl(m: re.Match) -> str:
        expr = m.group(1)
        return f"get_file_url({expr})"

    new = RE_ANY_PATH.sub(_repl, tmp)
    count = len(list(RE_ANY_PATH.finditer(tmp)))
    return new, count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="aplica as mudanças (senão, só relata)")
    parser.add_argument("--replace-urls", action="store_true", help="além do open(... .path ...), troca .path -> get_file_url(...) (revisar com cuidado)")
    args = parser.parse_args()

    total_open_repl = 0
    total_url_repl = 0
    reported_any_path = []

    for path in PROJECT_ROOT.rglob("*.py"):
        if should_skip(path):
            continue

        original = path.read_text(encoding="utf-8", errors="ignore")
        new = original

        # 1) Trocas seguras open(... .path ...)
        new, cnt_open = replace_open_path(new)
        if cnt_open:
            total_open_repl += cnt_open

        # 2) Reportar usos de .path (para revisão)
        any_paths = list(RE_ANY_PATH.finditer(new))
        if any_paths:
            # Filtra os que restaram (após a etapa 1)
            reported_any_path.append((path, [m.group(0) for m in any_paths]))

        # 3) Opcional: trocar .path -> get_file_url(...)
        cnt_url = 0
        if args.replace_urls and any_paths:
            new2, cnt_url = replace_path_with_get_url(new)
            if cnt_url:
                new = new2
                total_url_repl += cnt_url

        # 4) Se houve alguma troca, garante import
        if (cnt_open or cnt_url) and new != original:
            lines = new.splitlines(keepends=True)
            lines = ensure_import(lines, want_get=bool(args.replace_urls))
            new = "".join(lines)

        # 5) Escrever arquivo?
        if args.apply and new != original:
            backup = path.with_suffix(path.suffix + ".bak")
            if not backup.exists():
                backup.write_text(original, encoding="utf-8")
            path.write_text(new, encoding="utf-8")

    # Relatório
    print("== Refatoração storage-safe ==")
    print(f"- Substituições seguras em open(... .path ...): {total_open_repl}")
    if args.replace_urls:
        print(f"- Substituições adicionais .path -> get_file_url(...): {total_url_repl}")
    else:
        print("- (Modo conservador) Não trocamos .path fora de open(); veja os itens abaixo para revisar.")

    if reported_any_path:
        print("\nArquivos com usos de '.path' a revisar:")
        for p, items in reported_any_path:
            # lista única por arquivo
            uniq = sorted(set(items))
            print(f"  - {p}: {', '.join(uniq)}")
    else:
        print("\nSem usos remanescentes de '.path'.")

    print("\nDica: rode com --apply para aplicar e gere um commit dedicado.")
    if not args.apply:
        print("     (Dry-run: nada foi modificado.)")

if __name__ == "__main__":
    sys.exit(main())
