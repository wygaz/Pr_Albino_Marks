import csv
import re
import argparse
from pathlib import Path
from docx import Document

WS_RE = re.compile(r"\s+")

def first_paragraphs_summary(docx_path: Path, n_par=5, max_chars=420) -> str:
    doc = Document(str(docx_path))
    paras = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        t = WS_RE.sub(" ", t).strip()
        if not t:
            continue
        paras.append(t)
        if len(paras) >= n_par:
            break

    if not paras:
        return ""

    text = " ".join(paras)
    text = WS_RE.sub(" ", text).strip()

    if len(text) > max_chars:
        cut = text[:max_chars]
        last_dot = cut.rfind(".")
        if last_dot > 120:
            cut = cut[:last_dot+1]
        text = cut

    # 2–3 linhas
    if len(text) > 260:
        return text[:130].rstrip() + "\n" + text[130:260].strip() + ("\n" + text[260:].strip() if len(text) > 260 else "")
    if len(text) > 130:
        return text[:130].rstrip() + "\n" + text[130:].strip()
    return text

def main():
    ap = argparse.ArgumentParser(description="Gera prompts de imagem a partir do manifest.csv da série.")
    ap.add_argument("--data-root", default="", help="Pasta 'anexos_filtrados' (DataRoot). Se vazio, tenta repo/Apenas_Local/anexos_filtrados.")
    ap.add_argument("--series", help="Nome da série (default: última em .last_series.txt)")
    ap.add_argument("--npar", type=int, default=5, help="Qtde parágrafos (default: 5)")
    ap.add_argument("--maxchars", type=int, default=420, help="Corte máximo do resumo (default: 420)")
    args = ap.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    base = resolve_data_root(args.data_root, scripts_dir)
    series_root = base / 'SERIES'

    last_series_file = scripts_dir / ".last_series.txt"
    last_series = last_series_file.read_text(encoding="utf-8", errors="ignore").strip() if last_series_file.exists() else ""

    series_name = (args.series or "").strip() or last_series
    if not series_name:
        series_name = input(f"Nome da série [default: {last_series or '---'}]: ").strip() or last_series

    if not series_name:
        raise SystemExit("Informe o nome da série (ou rode consolidar_serie_por_esboco.py antes).")

    series_dir = series_root / series_name
    manifest_path = series_dir / "manifest.csv"
    if not manifest_path.exists():
        raise SystemExit(f"manifest.csv não encontrado em: {manifest_path}")

    docx_dir = series_dir / "DOCX"
    out_csv = series_dir / "prompts_imagens.csv"
    out_txt = series_dir / "prompts_imagens.txt"

    with open(manifest_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))


    prompts = []

    seen = set()

    for row in rows:
        if (row.get("status") or "").strip().upper() != "OK":
            continue

        docx_name = Path(row["destino_docx"]).name if row.get("destino_docx") else ""
        docx_path = docx_dir / docx_name
        if not docx_path.exists():
            continue

        titulo = docx_path.stem
        resumo = first_paragraphs_summary(docx_path, n_par=args.npar, max_chars=args.maxchars)

        prompt = (
            f"Ilustração de capa (SEM texto/SEM letras/SEM números). "
            f"Série: {series_name}. Artigo: {titulo}. "
            f"Contexto (resumo): {resumo}. "
            f"Estilo: pintura digital semi-realista, composição cinematográfica, luz suave, paleta sóbria, "
            f"tema bíblico/histórico, atmosfera reverente, alta qualidade, sem marcas d'água, sem tipografia."
        )

        arquivo = f"{titulo}.png"
        key = arquivo.lower()
        if key in seen:
            continue
        seen.add(key)

        prompts.append({
            "ordem": row.get("ordem"),
            "arquivo_sugerido": f"{titulo}.png",
            "titulo": titulo,
            "prompt": prompt
        })

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["ordem","arquivo_sugerido","titulo","prompt"], delimiter=";")
        w.writeheader()
        w.writerows(prompts)

    with open(out_txt, "w", encoding="utf-8") as f:
        for p in prompts:
            ordem = int(p["ordem"] or 0)
            f.write(f"### {p['ordem']} {p['arquivo_sugerido']}\n")
            f.write(p["prompt"] + "\n\n---\n\n")

    print("✅ Prompts gerados:")
    print(" -", out_csv)
    print(" -", out_txt)

if __name__ == "__main__":
    main()


# =========================
# UTIL: localizar raiz do repo (manage.py/.git)
# =========================
def find_repo_root(start: Path, max_levels: int = 10) -> Path | None:
    cur = start
    for _ in range(max_levels + 1):
        if (cur / 'manage.py').exists() or (cur / '.git').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def resolve_data_root(arg_value: str | None, scripts_dir: Path) -> Path:
    """
    Resolve a pasta 'anexos_filtrados' (DataRoot).
    - Se o usuário passou --data-root: usa ele
    - Senão: tenta <RepoRoot>/Apenas_Local/anexos_filtrados
    - Fallback: comportamento legado (scripts_dir.parent)
    """
    if arg_value and str(arg_value).strip():
        return Path(arg_value).expanduser().resolve()

    repo = find_repo_root(scripts_dir)
    if repo:
        cand = (repo / 'Apenas_Local' / 'anexos_filtrados')
        if cand.exists():
            return cand.resolve()

    return scripts_dir.parent.resolve()
