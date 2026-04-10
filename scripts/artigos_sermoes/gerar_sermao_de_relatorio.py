import argparse
import re
import unicodedata
from pathlib import Path
from openai import OpenAI
from preparacao_do_ambiente_operacional import canonical_index, extract_series_from_outline, match_candidate
from artigos_operacional_utils import strip_editorial_prefixes


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_workspace_stem(value: str) -> str:
    text = Path(value or "").stem
    text = re.sub(r"__dossie$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"__relatorio_tecnico__.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"__sermao__.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\d{1,3}__+", "", text)
    text = re.sub(r"^\d{1,3}_+", "", text)
    text = strip_editorial_prefixes(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" _-") or "sermao"


def ascii_slug(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value or "sermao"


def canonical_base_stem(value: str) -> str:
    raw = Path(value or "").stem
    match = re.match(r"^(?P<prefix>\d{1,3})__(?P<body>.+)$", raw)
    prefix = f"{int(match.group('prefix')):02d}__" if match else ""
    body = match.group("body") if match else raw
    return f"{prefix}{ascii_slug(clean_workspace_stem(body))}"


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


def default_esboco_path() -> Path:
    root = repo_root_from_here()
    return root / "Apenas_Local" / "anexos_filtrados" / "Docs" / "ESBOCO_Geral_Series_1_a_4.docx"


def relatorio_title_candidates(path: Path, text: str) -> list[str]:
    candidates = [clean_workspace_stem(path.stem)]
    match = re.search(r"(?im)^[-*]\s*T[íi]tulo:\s*(.+)$", text)
    if match:
        candidates.append(match.group(1).strip())
    unique = []
    for item in candidates:
        if item and item not in unique:
            unique.append(item)
    return unique


def resolve_series_outdir(relatorio_path: Path, relatorio_text: str, requested_outdir: Path, esboco: Path) -> Path:
    requested = requested_outdir.resolve()
    if requested.name != "markdown":
        return requested
    idx = canonical_index(extract_series_from_outline(esboco))
    item, _method, _score = match_candidate(relatorio_title_candidates(relatorio_path, relatorio_text), idx, cutoff=0.84)
    if not item:
        return requested
    serie_dir = item.serie_dir_name.split("__", 1)[1] if "__" in item.serie_dir_name else ascii_slug(item.serie_dir_name)
    return requested / serie_dir


def build_prompt_sermao(relatorio: str) -> str:
    return f"""IDIOMA: Português do Brasil.

TAREFA:
Produzir um SERMÃO COMPLETO com base EXCLUSIVAMENTE no RELATÓRIO TÉCNICO fornecido.

OBJETIVO:
Transformar o conteúdo analítico do relatório em um sermão fiel, bíblico, doutrinariamente sólido, bem organizado, com tom pastoral equilibrado e fechamento natural.

DIRETRIZES OBRIGATÓRIAS:
- Ser fiel ao relatório técnico recebido.
- Não inventar doutrinas, citações, fontes, páginas ou referências externas.
- Não contradizer a tese central, a linha argumentativa ou os limites hermenêuticos definidos no relatório.
- Não usar linguagem agressiva, sensacionalista ou caricatural.
- Manter sobriedade bíblica, clareza pastoral e progressão lógica.
- O sermão deve ter começo, desenvolvimento e encerramento orgânicos.
- O encerramento não pode ser abrupto.
- O sermão deve respeitar o verso-chave, o texto bíblico central, o tom e o tipo de fechamento sugeridos no relatório.
- Incluir uma sugestão breve de oração antes da leitura do texto bíblico central.
- Não mencionar que o texto foi gerado a partir de um relatório técnico.

ESTRUTURA OBRIGATÓRIA DO SERMÃO:

1) TÍTULO DO SERMÃO
- Usar o título significativo sugerido no relatório, salvo se houver razão muito forte para pequeno refinamento sem mudar o sentido.

2) VERSO-CHAVE
- Exibir logo abaixo do título.
- Mostrar a referência e o texto do verso.

3) SUGESTÃO BREVE DE ORAÇÃO
- Uma oração curta, reverente e diretamente conectada ao tema.

4) LEITURA DO TEXTO BÍBLICO CENTRAL
- Indicar claramente o texto bíblico central sugerido.

5) INTRODUÇÃO
- Introduzir o tema com clareza, conexão e naturalidade.
- Preparar o auditório para a tese central sem exageros.

6) DESENVOLVIMENTO
- Seguir a linha argumentativa do relatório.
- Organizar o sermão em blocos coerentes.
- Preservar a ordem lógica.
- Destacar os fundamentos bíblicos centrais.
- Explicar com clareza, sem transformar o texto em aula fria nem em discurso emotivo demais.

7) APLICAÇÃO
- Inserir aplicações espirituais e pastorais coerentes com o conteúdo apresentado.
- Não introduzir tese nova aqui.

8) CONCLUSÃO
- Conduzir o encerramento de forma progressiva.
- Retomar a tese central.
- Fechar com coerência, reverência e força espiritual equilibrada.
- Evitar final seco ou apressado.

IMPORTANTE:
- Não criar tom artificial.
- Não repetir excessivamente as mesmas ideias.
- Não usar jargão técnico em excesso.
- Não fazer acusação confessional agressiva.
- Não criar apelo apelativo.
- O sermão deve soar pregável, sólido e natural.

RELATÓRIO TÉCNICO:
{relatorio}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relatorio", required=True, help="Arquivo .md do relatório técnico")
    ap.add_argument("--outdir", required=True, help="Pasta de saída")
    ap.add_argument("--esboco", default="")
    ap.add_argument("--model", default="gpt-5")
    args = ap.parse_args()

    relatorio_path = Path(args.relatorio)
    relatorio = read_text(relatorio_path)
    esboco = Path(args.esboco).resolve() if args.esboco else default_esboco_path()
    outdir = resolve_series_outdir(relatorio_path, relatorio, Path(args.outdir), esboco)
    outdir.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    prompt = build_prompt_sermao(relatorio)
    resp = client.responses.create(model=args.model, input=prompt)

    base_name = canonical_base_stem(relatorio_path.stem)
    outpath = outdir / f"{base_name}__sermao.md"
    outpath.write_text(resp.output_text, encoding="utf-8")
    print(f"[OK] sermao: {outpath}")


if __name__ == "__main__":
    main()
