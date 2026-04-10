import argparse
import base64
import os
import re
import time
from pathlib import Path

from openai import OpenAI


WINDOWS_BAD_CHARS = r'<>:"/\\|?*'


def sanitize_filename(name: str) -> str:
    """
    Remove caracteres inválidos no Windows e normaliza espaços/pontos finais.
    Mantém extensão (.png/.jpg/.jpeg/.webp) se existir.
    """
    name = name.strip()

    # separa extensão
    m = re.match(r"^(.*?)(\.(png|jpg|jpeg|webp))?$", name, flags=re.IGNORECASE)
    base = (m.group(1) or "").strip()
    ext = (m.group(2) or ".png").lower()

    # remove chars proibidos
    base = re.sub(f"[{re.escape(WINDOWS_BAD_CHARS)}]", "", base)

    # evita nomes vazios
    base = base.strip().strip(".")
    if not base:
        base = "imagem"

    # Windows não gosta de espaço/ponto no fim
    base = base.rstrip(" .")

    return f"{base}{ext}"


def parse_prompts_txt(path: Path):
    """
    Lê um arquivo no formato:
    ### 1 TITULO.png
    prompt...
    ---
    ### 2 OUTRO.png
    prompt...
    ---
    Retorna [(filename, prompt), ...]
    """
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()

    items = []
    cur_name = None
    cur_lines = []

    def flush():
        nonlocal cur_name, cur_lines
        if cur_name and cur_lines:
            prompt = " ".join([l.strip() for l in cur_lines if l.strip()])

            # remove numeração inicial do nome do arquivo, se houver
            name = re.sub(r"^\d+\s*\|\s*", "", cur_name).strip()  # remove "1 | "
            name = re.sub(r"^\d+\s+", "", name).strip()           # fallback antigo
            name = name.lstrip("|").strip()                        # segurança extra

            # garante extensão e sanitiza
            if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                name += ".png"
            name = sanitize_filename(name)

            items.append((name, prompt))

        cur_name = None
        cur_lines = []

    for line in text:
        s = line.rstrip()

        if s.strip().startswith("###"):
            flush()
            cur_name = s.strip().lstrip("#").strip()
            continue

        if s.strip() == "---":
            flush()
            continue

        if cur_name:
            cur_lines.append(s)

    flush()
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="Pasta da série (default: .)")
    ap.add_argument("--prompts", default="prompts_imagens.txt",
                    help="Arquivo de prompts (default: prompts_imagens.txt)")
    ap.add_argument("--out", default="IMG", help="Pasta de saída (default: IMG)")
    ap.add_argument("--model", default="gpt-image-1.5", help="Modelo (default: gpt-image-1.5)")

    # ✅ WEB BARATO por padrão
    ap.add_argument("--size", default="1024x1024",
                    help="Tamanho (default: 1024x1024). Ex: 1536x1024")
    ap.add_argument("--quality", default="low", choices=["low", "medium", "high", "auto"],
                    help="Qualidade (default: low)")

    ap.add_argument("--run", action="store_true", help="Executa de fato a geração via API. Sem --run, apenas lista o que faria (sem consumir).")

    ap.add_argument("--overwrite", action="store_true", help="Sobrescrever imagens existentes")
    ap.add_argument("--sleep", type=float, default=1.2, help="Pausa entre requests (segundos)")
    ap.add_argument("--limit", type=int, default=0, help="Processa no máximo N prompts (0=sem limite).")

    args = ap.parse_args()

    series_dir = Path(args.dir).resolve()
    prompts_path = series_dir / args.prompts
    out_dir = series_dir / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not prompts_path.exists():
        raise SystemExit(f"Não achei: {prompts_path}")

    items = parse_prompts_txt(prompts_path)
    if args.limit and args.limit > 0:
        items = items[:args.limit]

    print(f"Prompts encontrados: {len(items)}")
    print(f"Config: model={args.model} size={args.size} quality={args.quality}")
    if not args.run:
        print('ℹ️  Modo simulação (sem --run): nenhuma chamada à API será feita.')
        for i, (filename, _) in enumerate(items, start=1):
            out_path = out_dir / filename
            if out_path.exists() and not args.overwrite:
                print(f'[{i}/{len(items)}] Já existe: {out_path.name}')
            else:
                print(f'[{i}/{len(items)}] Geraria: {out_path.name}')
        print("\n✅ Simulação concluída.")
        return

    # (opcional, mas útil) diagnosticar chave
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        raise SystemExit('❌ OPENAI_API_KEY não está definida no ambiente.')
    if any(c.isspace() for c in api_key):
        raise SystemExit('❌ OPENAI_API_KEY contém espaço/quebra de linha. Cole novamente.')

    client = OpenAI(api_key=api_key)

    ok = 0
    for i, (filename, prompt) in enumerate(items, start=1):
        out_path = out_dir / filename

        if out_path.exists() and not args.overwrite:
            print(f"[{i}/{len(items)}] Pular (já existe): {out_path.name}")
            continue

        print(f"[{i}/{len(items)}] Gerando: {out_path.name}")

        try:
            img = client.images.generate(
                model=args.model,
                prompt=prompt,
                size=args.size,
                quality=args.quality,     # ✅ aqui
                output_format="png",
            )
            image_bytes = base64.b64decode(img.data[0].b64_json)
            out_path.write_bytes(image_bytes)
            ok += 1
        except Exception as e:
            print(f"  ❌ Falhou: {out_path.name} -> {e}")

        time.sleep(args.sleep)

    print(f"\n✅ Concluído. Geradas: {ok}/{len(items)} em {out_dir}")


if __name__ == "__main__":
    main()
