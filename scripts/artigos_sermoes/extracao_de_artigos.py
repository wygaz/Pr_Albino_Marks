from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(8):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print("\n[RUN]", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd))
    if proc.returncode != 0:
        raise RuntimeError(f"Falha no comando: {' '.join(cmd)}")


def copy_flatten_docs(source_dirs: list[Path], flat_dir: Path) -> int:
    flat_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for path in sorted(source_dir.glob("*.docx")):
            dst = flat_dir / path.name
            shutil.copy2(path, dst)
            copied += 1
    return copied


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extracao de artigos: baixa anexos e monta a entrada plana para a preparacao operacional."
    )
    parser.add_argument("--ini", default="2024-09-20", help="Data inicial AAAA-MM-DD da baixa principal.")
    parser.add_argument("--fim", default=datetime.date.today().isoformat(), help="Data final AAAA-MM-DD da baixa principal.")
    parser.add_argument("--ini-complementar", help="Data inicial AAAA-MM-DD da baixa complementar.")
    parser.add_argument("--fim-complementar", help="Data final AAAA-MM-DD da baixa complementar.")
    parser.add_argument("--lote", required=True, help="Nome do lote base em Apenas_Local/anexos_filtrados.")
    parser.add_argument("--baixar-esbocos", action="store_true", help="Tambem faz a baixa separada dos esbocos.")
    parser.add_argument("--lote-esbocos", help="Nome do lote dos esbocos. Default: <lote>_esbocos")
    parser.add_argument("--nao-baixar-artigos", action="store_true", help="Pula a baixa de artigos e usa o lote ja existente.")
    parser.add_argument("--complementar-dir", action="append", default=[], help="Diretorio adicional com DOCX para complementar o lote.")
    parser.add_argument("--python-exe", default="", help="Interpretador Python. Default: <repo>\\venv\\Scripts\\python.exe")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    scripts_dir = Path(__file__).resolve().parent
    python_exe = Path(args.python_exe) if args.python_exe else root / "venv" / "Scripts" / "python.exe"
    baixar_script = scripts_dir / "baixar_anexos_pralbino_esbocos.py"

    anexos_root = root / "Apenas_Local" / "anexos_filtrados"
    lote_dir = anexos_root / args.lote
    lote_esbocos = args.lote_esbocos or f"{args.lote}_esbocos"
    lote_esbocos_dir = anexos_root / lote_esbocos

    if args.baixar_esbocos:
        run_cmd(
            [
                str(python_exe),
                str(baixar_script),
                "--modo",
                "esbocos",
                "--so",
                ".docx",
                "--ini",
                args.ini,
                "--fim",
                args.fim,
                "--lote",
                lote_esbocos,
            ],
            cwd=root,
        )

    if not args.nao_baixar_artigos:
        run_cmd(
            [
                str(python_exe),
                str(baixar_script),
                "--modo",
                "artigos",
                "--so",
                ".docx",
                "--ini",
                args.ini,
                "--fim",
                args.fim,
                "--lote",
                args.lote,
            ],
            cwd=root,
        )
        if args.ini_complementar and args.fim_complementar:
            run_cmd(
                [
                    str(python_exe),
                    str(baixar_script),
                    "--modo",
                    "artigos",
                    "--so",
                    ".docx",
                    "--ini",
                    args.ini_complementar,
                    "--fim",
                    args.fim_complementar,
                    "--lote",
                    args.lote,
                ],
                cwd=root,
            )

    if not lote_dir.exists():
        raise FileNotFoundError(f"Lote de artigos nao encontrado: {lote_dir}")

    flat_dir = lote_dir / "_entrada_preparacao"
    if flat_dir.exists():
        shutil.rmtree(flat_dir)
    copied = copy_flatten_docs([lote_dir], flat_dir)
    for extra in [Path(p).resolve() for p in args.complementar_dir]:
        copied += copy_flatten_docs([extra], flat_dir)

    print(f"\n[OK] DOCX copiados para entrada plana: {copied}")
    print(f"[OK] Lote artigos: {lote_dir}")
    print(f"[OK] Entrada plana: {flat_dir}")
    if args.baixar_esbocos:
        print(f"[OK] Lote de esbocos: {lote_esbocos_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
