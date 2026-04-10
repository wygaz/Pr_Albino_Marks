#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

SCRIPT_EXTS = {".py", ".ps1", ".psm1", ".bat", ".cmd"}
DEFAULT_INCLUDE_DIRS = [
    ".",
    "scripts",
    "Utilitarios",
    "Utilitarios/Scripts",
    "Apenas_Local/scripts",
    "Apenas_Local/anexos_filtrados/Scripts",
    "Apenas_Local/anexos_filtrados/sermoes/producao",
]
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "ENV",
    "__pycache__",
    "node_modules",
    "media",
    "staticfiles",
    "_pacotes_chatgpt",
    "_quarentena",
    "_backup_sanitizacao",
    "_sanitizados_preview",
    "backups",
    "pgdata",
    "postgres-data",
}

SENSITIVE_NAME_HINTS = {
    "password": "DB_PASSWORD",
    "passwd": "DB_PASSWORD",
    "pwd": "DB_PASSWORD",
    "secret_key": "SECRET_KEY",
    "api_key": "API_KEY",
    "apikey": "API_KEY",
    "token": "API_TOKEN",
    "access_key": "ACCESS_KEY",
    "access_key_id": "ACCESS_KEY_ID",
    "secret_access_key": "SECRET_ACCESS_KEY",
    "database_url": "DATABASE_URL",
    "db_url": "DATABASE_URL",
    "conn_str": "DATABASE_URL",
    "connection_string": "DATABASE_URL",
}

SPECIAL_ENV_MAP = {
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME": "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION_NAME": "AWS_S3_REGION_NAME",
    "DATABASE_URL": "DATABASE_URL",
    "DATABASE_PUBLIC_URL": "DATABASE_PUBLIC_URL",
    "SECRET_KEY": "SECRET_KEY",
    "S3_BUCKET_NAME": "S3_BUCKET_NAME",
}



def split_name_tokens(name: str) -> list[str]:
    interim = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    interim = interim.replace("-", "_")
    return [p.lower() for p in interim.split("_") if p]


EXCLUDED_NAME_TOKENS = {"name", "file", "path", "dir", "directory", "help", "template", "application", "storage", "prefix", "suffix", "out", "saida"}


def has_sensitive_name(name: str) -> bool:
    tokens = split_name_tokens(name)
    token_set = set(tokens)
    if token_set & EXCLUDED_NAME_TOKENS:
        return False
    if any(t in token_set for t in ["password", "passwd", "pwd", "token"]):
        return True
    if "database" in token_set and "url" in token_set:
        return True
    if "db" in token_set and "url" in token_set:
        return True
    if "api" in token_set and "key" in token_set:
        return True
    if "access" in token_set and "key" in token_set:
        return True
    if "access" in token_set and "key" in token_set and "id" in token_set:
        return True
    if "secret" in token_set and "key" in token_set:
        return True
    if "secret" in token_set and "access" in token_set and "key" in token_set:
        return True
    return False


def value_looks_like_secret(value: str) -> bool:
    v = value.strip()
    if DB_LITERAL_RE.search(v):
        return True
    if re.fullmatch(r"AKIA[0-9A-Z]{16}", v):
        return True
    if re.fullmatch(r"sk-[A-Za-z0-9]{16,}", v):
        return True
    return False



URL_SECRET_RE = re.compile(
    r"(?P<q>['\"])(?P<url>(?:postgres(?:ql)?|mysql|redis|amqp)://[^'\"\s]+)(?P=q)",
    re.IGNORECASE,
)

PY_ASSIGN_RE = re.compile(
    r"(?P<prefix>\b(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)(?P<q>['\"])(?P<value>[^'\"\n]+)(?P=q)"
)
PY_KWARG_RE = re.compile(
    r"(?P<prefix>\b(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)(?P<q>['\"])(?P<value>[^'\"\n]+)(?P=q)(?P<suffix>\s*[,\)])"
)
PS_ASSIGN_RE = re.compile(
    r"(?P<indent>\s*)(?P<lhs>\$(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)(?P<q>['\"])(?P<value>[^'\"\n]+)(?P=q)"
)

DB_LITERAL_RE = re.compile(r"(?:postgres(?:ql)?|mysql|redis|amqp)://", re.IGNORECASE)
LIKELY_SECRET_VALUE_RE = re.compile(
    r"(^AKIA[0-9A-Z]{16}$)|"
    r"(^sk-[A-Za-z0-9]{16,}$)|"
    r"([A-Za-z0-9/+_=.-]{24,})|"
    r"([A-Za-z][A-Za-z0-9_\-]{2,}://[^\s]+)",
    re.IGNORECASE,
)


@dataclass
class Finding:
    path: str
    line_no: int
    lang: str
    kind: str
    var_name: str
    env_name: str
    original: str
    replacement: str
    applied: bool = False


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


def infer_env_name(var_name: str, value: str, path: Path) -> str:
    upper = var_name.upper()
    if upper in SPECIAL_ENV_MAP:
        return SPECIAL_ENV_MAP[upper]

    normalized = var_name.lower()
    if normalized in SENSITIVE_NAME_HINTS:
        return SENSITIVE_NAME_HINTS[normalized]

    tokens = set(split_name_tokens(var_name))
    if {"api", "key"} <= tokens and "openai" in str(path).lower():
        return "OPENAI_API_KEY"
    if {"token"} <= tokens and "railway" in str(path).lower():
        return "RAILWAY_TOKEN"
    if {"access", "key", "id"} <= tokens:
        return "AWS_ACCESS_KEY_ID"
    if {"secret", "access", "key"} <= tokens:
        return "AWS_SECRET_ACCESS_KEY"
    if {"secret", "key"} <= tokens:
        return "SECRET_KEY"
    if {"database", "url"} <= tokens or {"db", "url"} <= tokens:
        return "DATABASE_URL"
    if {"password"} <= tokens or {"passwd"} <= tokens or {"pwd"} <= tokens:
        return "DB_PASSWORD"

    if DB_LITERAL_RE.search(value):
        return "DATABASE_URL"

    return upper


# Keep replacements conservative by default.
def is_sensitive_candidate(var_name: str, value: str) -> bool:
    return has_sensitive_name(var_name) or value_looks_like_secret(value)


def read_text(path: Path) -> str | None:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    return None


def ensure_import_os(text: str) -> str:
    if re.search(r"^\s*import\s+os\b", text, re.MULTILINE) or re.search(r"^\s*from\s+os\s+import\b", text, re.MULTILINE):
        return text

    lines = text.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if insert_at < len(lines) and re.match(r"^[rubf]*[\"']{3}", lines[insert_at].strip(), re.IGNORECASE):
        quote = lines[insert_at].strip()[:3]
        for i in range(insert_at + 1, len(lines)):
            if quote in lines[i]:
                insert_at = i + 1
                break
    lines.insert(insert_at, "import os\n")
    return "".join(lines)


def line_no_from_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def replace_python(text: str, path: Path, findings: list[Finding]) -> str:
    original = text

    def repl_url(m: re.Match[str]) -> str:
        url = m.group("url")
        env_name = "DATABASE_URL"
        replacement = f'os.getenv("{env_name}", "")'
        findings.append(Finding(
            path=str(path),
            line_no=line_no_from_pos(original, m.start()),
            lang="python",
            kind="url_literal",
            var_name="url",
            env_name=env_name,
            original=url,
            replacement=replacement,
        ))
        return replacement

    text = URL_SECRET_RE.sub(repl_url, text)

    def repl_assign(m: re.Match[str]) -> str:
        var = m.group("var")
        value = m.group("value")
        if not is_sensitive_candidate(var, value):
            return m.group(0)
        env_name = infer_env_name(var, value, path)
        replacement = f'{m.group("prefix")}os.getenv("{env_name}", "")'
        findings.append(Finding(
            path=str(path),
            line_no=line_no_from_pos(original, m.start()),
            lang="python",
            kind="assignment_literal",
            var_name=var,
            env_name=env_name,
            original=value,
            replacement=replacement,
        ))
        return replacement

    def repl_kwarg(m: re.Match[str]) -> str:
        var = m.group("var")
        value = m.group("value")
        if not is_sensitive_candidate(var, value):
            return m.group(0)
        env_name = infer_env_name(var, value, path)
        replacement = f'{m.group("prefix")}os.getenv("{env_name}", ""){m.group("suffix")}'
        findings.append(Finding(
            path=str(path),
            line_no=line_no_from_pos(original, m.start()),
            lang="python",
            kind="kwarg_literal",
            var_name=var,
            env_name=env_name,
            original=value,
            replacement=replacement.rstrip(),
        ))
        return replacement

    # kwargs first, then plain assignment.
    text = PY_KWARG_RE.sub(repl_kwarg, text)
    text = PY_ASSIGN_RE.sub(repl_assign, text)

    if text != original:
        text = ensure_import_os(text)
    return text


def replace_powershell(text: str, path: Path, findings: list[Finding]) -> str:
    original = text

    def repl_assign(m: re.Match[str]) -> str:
        var = m.group("var")
        value = m.group("value")
        if not is_sensitive_candidate(var, value):
            return m.group(0)
        env_name = infer_env_name(var, value, path)
        replacement = f'{m.group("indent")}${var} = $env:{env_name}'
        findings.append(Finding(
            path=str(path),
            line_no=line_no_from_pos(original, m.start()),
            lang="powershell",
            kind="assignment_literal",
            var_name=var,
            env_name=env_name,
            original=value,
            replacement=replacement.strip(),
        ))
        return replacement

    return PS_ASSIGN_RE.sub(repl_assign, text)


def iter_script_files(root: Path, include_dirs: Iterable[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    for inc in include_dirs:
        base = (root / inc).resolve()
        if not base.exists():
            continue
        if base.is_file() and base.suffix.lower() in SCRIPT_EXTS:
            if base not in seen:
                seen.add(base)
                yield base
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SCRIPT_EXTS:
                continue
            parts = set(path.parts)
            if parts & DEFAULT_EXCLUDE_DIRS:
                continue
            if path not in seen:
                seen.add(path)
                yield path


def backup_file(root: Path, path: Path, backup_root: Path) -> Path:
    rel = path.resolve().relative_to(root.resolve())
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def write_report(out_dir: Path, findings: list[Finding]) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "relatorio_segredos.csv"
    md_path = out_dir / "relatorio_segredos.md"
    env_template_path = out_dir / ".env.segredos_template"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["arquivo", "linha", "linguagem", "tipo", "variavel", "env", "original_sha1", "replacement", "aplicado"])
        for item in findings:
            w.writerow([
                item.path,
                item.line_no,
                item.lang,
                item.kind,
                item.var_name,
                item.env_name,
                sha1_text(item.original),
                item.replacement,
                "1" if item.applied else "0",
            ])

    grouped_envs: dict[str, list[Finding]] = {}
    for item in findings:
        grouped_envs.setdefault(item.env_name, []).append(item)

    with env_template_path.open("w", encoding="utf-8") as f:
        f.write("# Template gerado automaticamente. Preencha os valores reais fora do Git.\n")
        for env_name in sorted(grouped_envs):
            f.write(f"{env_name}=\n")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Relatório de segredos em scripts\n\n")
        f.write(f"Total de ocorrências: **{len(findings)}**\n\n")
        if not findings:
            f.write("Nenhuma ocorrência detectada pelos padrões conservadores.\n")
        else:
            by_file: dict[str, list[Finding]] = {}
            for item in findings:
                by_file.setdefault(item.path, []).append(item)
            for file_path in sorted(by_file):
                f.write(f"## {file_path}\n\n")
                for item in sorted(by_file[file_path], key=lambda x: x.line_no):
                    f.write(
                        f"- linha {item.line_no}: `{item.var_name}` → `{item.env_name}` ({item.lang}, {item.kind}, aplicado={item.applied})\n"
                    )
                f.write("\n")
            f.write("## Variáveis sugeridas para .env\n\n")
            for env_name, items in sorted(grouped_envs.items()):
                f.write(f"- `{env_name}` ← {len(items)} ocorrência(s)\n")

    return csv_path, md_path, env_template_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rastreia e sanitiza segredos hardcoded em scripts Python/PowerShell."
    )
    parser.add_argument("--root", default=".", help="Raiz do projeto.")
    parser.add_argument(
        "--include-dir",
        action="append",
        dest="include_dirs",
        help="Diretório adicional para varrer. Pode repetir.",
    )
    parser.add_argument(
        "--preview-dir",
        default="_sanitizados_preview",
        help="Pasta para cópias sanitizadas em modo preview.",
    )
    parser.add_argument(
        "--report-dir",
        default="_diagnosticos_segredos",
        help="Pasta de relatórios.",
    )
    parser.add_argument(
        "--backup-dir",
        default="_backup_sanitizacao",
        help="Pasta de backup para modo inplace.",
    )
    parser.add_argument(
        "--apply-preview",
        action="store_true",
        help="Gera cópias sanitizadas em uma pasta preview, sem alterar os originais.",
    )
    parser.add_argument(
        "--apply-inplace",
        action="store_true",
        help="Altera os arquivos originais após criar backup.",
    )
    args = parser.parse_args()

    if args.apply_preview and args.apply_inplace:
        raise SystemExit("Use apenas um modo de aplicação: --apply-preview OU --apply-inplace.")

    root = Path(args.root).resolve()
    include_dirs = list(dict.fromkeys(DEFAULT_INCLUDE_DIRS + (args.include_dirs or [])))
    preview_root = root / args.preview_dir
    backup_root = root / args.backup_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    report_root = root / args.report_dir / datetime.now().strftime("%Y%m%d_%H%M%S")

    findings: list[Finding] = []
    changed_count = 0
    scanned_count = 0

    for path in iter_script_files(root, include_dirs):
        scanned_count += 1
        text = read_text(path)
        if text is None:
            continue
        ext = path.suffix.lower()
        local_findings: list[Finding] = []
        if ext == ".py":
            new_text = replace_python(text, path.relative_to(root), local_findings)
        elif ext in {".ps1", ".psm1"}:
            new_text = replace_powershell(text, path.relative_to(root), local_findings)
        else:
            new_text = text

        changed = new_text != text and bool(local_findings)
        if changed:
            changed_count += 1
            if args.apply_preview:
                dest = preview_root / path.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(new_text, encoding="utf-8", newline="\n")
                for item in local_findings:
                    item.applied = True
            elif args.apply_inplace:
                backup_file(root, path, backup_root)
                path.write_text(new_text, encoding="utf-8", newline="\n")
                for item in local_findings:
                    item.applied = True

        findings.extend(local_findings)

    csv_path, md_path, env_template_path = write_report(report_root, findings)

    print("=== Varredura concluída ===")
    print(f"Raiz: {root}")
    print(f"Arquivos escaneados: {scanned_count}")
    print(f"Ocorrências detectadas: {len(findings)}")
    print(f"Arquivos com alteração possível: {changed_count}")
    print(f"Relatório CSV: {csv_path}")
    print(f"Relatório MD:  {md_path}")
    print(f"Env template:  {env_template_path}")
    if args.apply_preview:
        print(f"Preview sanitizado em: {preview_root}")
    if args.apply_inplace:
        print(f"Backup dos originais em: {backup_root}")
    print("Modo padrão é seguro: só diagnostica. Use --apply-preview antes de --apply-inplace.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
