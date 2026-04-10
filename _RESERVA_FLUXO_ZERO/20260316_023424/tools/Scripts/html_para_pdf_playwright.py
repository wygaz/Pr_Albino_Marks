import argparse
import sys
from pathlib import Path
from typing import Iterable, List

from playwright.sync_api import sync_playwright


def expand_inputs(items: Iterable[str], recursive: bool = False) -> List[Path]:
    paths: List[Path] = []
    for item in items:
        p = Path(item)
        if p.is_dir():
            pattern = "**/*.html" if recursive else "*.html"
            paths.extend(sorted(p.glob(pattern)))
        else:
            matches = sorted(Path().glob(item)) if any(ch in item for ch in "*?[]") else [p]
            for m in matches:
                if m.is_dir():
                    pattern = "**/*.html" if recursive else "*.html"
                    paths.extend(sorted(m.glob(pattern)))
                else:
                    paths.append(m)
    # remove duplicates preserving order
    seen = set()
    out = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen and p.suffix.lower() == ".html":
            seen.add(rp)
            out.append(rp)
    return out


def infer_mode(html_path: Path, html_text: str, explicit_mode: str) -> str:
    if explicit_mode in {"print", "screen"}:
        return explicit_mode
    name = html_path.name.lower()
    if "tablet" in name:
        return "screen"
    return "print"


def has_css_page_size(html_text: str) -> bool:
    lowered = html_text.lower()
    return "@page" in lowered and "size:" in lowered


def default_pdf_name(html_path: Path) -> str:
    return html_path.with_suffix(".pdf").name


def convert_file(
    html_path: Path,
    output_dir: Path | None,
    browser_name: str,
    mode: str,
    print_background: bool,
    scale: float,
    screen_format: str,
    width: str | None,
    height: str | None,
    margins: dict,
    timeout_ms: int,
) -> Path:
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    chosen_mode = infer_mode(html_path, html_text, mode)
    css_page = has_css_page_size(html_text)

    target_dir = output_dir if output_dir else html_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = target_dir / default_pdf_name(html_path)

    with sync_playwright() as p:
        browser_launcher = getattr(p, browser_name)
        browser = browser_launcher.launch(headless=True)
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="load", timeout=timeout_ms)
        page.emulate_media(media=chosen_mode)

        pdf_kwargs = {
            "path": str(pdf_path),
            "print_background": print_background,
            "scale": scale,
            "margin": margins,
        }

        if css_page:
            pdf_kwargs["prefer_css_page_size"] = True
        else:
            if chosen_mode == "screen":
                if width and height:
                    pdf_kwargs["width"] = width
                    pdf_kwargs["height"] = height
                else:
                    pdf_kwargs["format"] = screen_format
            else:
                # fallback conservador para HTML sem @page
                pdf_kwargs["format"] = "A4"

        page.pdf(**pdf_kwargs)
        browser.close()

    return pdf_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Converte arquivos HTML locais em PDF usando Playwright, respeitando "
            "@page quando presente e permitindo processamento em lote."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Arquivos .html, diretórios ou globs (*.html) a converter.",
    )
    parser.add_argument(
        "--outdir",
        help="Pasta de saída. Se omitido, grava o PDF ao lado de cada HTML.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Ao informar diretório, busca HTMLs recursivamente.",
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Navegador do Playwright a usar. Padrão: chromium.",
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "print", "screen"],
        help=(
            "Modo de mídia CSS. 'auto' usa screen para arquivos com 'tablet' no nome "
            "e print para os demais."
        ),
    )
    parser.add_argument(
        "--screen-format",
        default="A4",
        choices=["A4", "A5", "Letter", "Legal", "Tabloid", "Ledger", "A3", "A6"],
        help="Formato-padrão quando o HTML não tiver @page e o modo efetivo for screen.",
    )
    parser.add_argument("--width", help="Largura do PDF sem @page, ex.: 160mm")
    parser.add_argument("--height", help="Altura do PDF sem @page, ex.: 240mm")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Escala de renderização do PDF. Padrão: 1.0",
    )
    parser.add_argument(
        "--no-print-background",
        action="store_true",
        help="Desliga a impressão de fundos e cores de fundo.",
    )
    parser.add_argument("--margin-top", default="0")
    parser.add_argument("--margin-right", default="0")
    parser.add_argument("--margin-bottom", default="0")
    parser.add_argument("--margin-left", default="0")
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Timeout de abertura do HTML local. Padrão: 30000 ms.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    html_files = expand_inputs(args.inputs, recursive=args.recursive)
    if not html_files:
        print("[ERRO] Nenhum arquivo .html encontrado.")
        return 1

    outdir = Path(args.outdir).resolve() if args.outdir else None
    margins = {
        "top": args.margin_top,
        "right": args.margin_right,
        "bottom": args.margin_bottom,
        "left": args.margin_left,
    }

    print(f"[INFO] HTMLs encontrados: {len(html_files)}")
    for html in html_files:
        try:
            pdf = convert_file(
                html_path=html,
                output_dir=outdir,
                browser_name=args.browser,
                mode=args.mode,
                print_background=not args.no_print_background,
                scale=args.scale,
                screen_format=args.screen_format,
                width=args.width,
                height=args.height,
                margins=margins,
                timeout_ms=args.timeout_ms,
            )
            print(f"[OK] {html.name} -> {pdf}")
        except Exception as exc:
            print(f"[ERRO] {html}: {exc}")
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
