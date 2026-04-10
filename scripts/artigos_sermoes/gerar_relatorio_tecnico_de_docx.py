import argparse
import re
import unicodedata
from pathlib import Path
from docx import Document
from openai import OpenAI
from preparacao_do_ambiente_operacional import resolve_single_article_target
from artigos_operacional_utils import strip_editorial_prefixes


def clean_workspace_stem(value: str) -> str:
    text = Path(value or "").stem
    text = re.sub(r"__relatorio_tecnico__.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"__sermao__.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\d{1,3}__+", "", text)
    text = re.sub(r"^\d{1,3}_+", "", text)
    text = strip_editorial_prefixes(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" _-") or "documento"


def ascii_slug(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value or "documento"


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


def resolve_series_outdir(docx: Path, requested_outdir: Path, esboco: Path) -> Path:
    requested = requested_outdir.resolve()
    if requested.name != "markdown":
        return requested
    item, _method, _score, _titulo_final, _dst = resolve_single_article_target(
        arquivo=docx,
        outline=esboco,
        output_dir=requested.parent.parent / "artigos" / "series",
        cutoff=0.84,
    )
    serie_dir = item.serie_dir_name.split("__", 1)[1] if "__" in item.serie_dir_name else ascii_slug(item.serie_dir_name)
    return requested / serie_dir

def read_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)

def build_prompt_relatorio(text: str) -> str:
    return f"""IDIOMA: Português do Brasil.

TAREFA:
Produzir um RELATÓRIO TEOLÓGICO TÉCNICO, e não um sermão, com base exclusivamente no TEXTO-FONTE fornecido.

OBJETIVO:
Mapear com fidelidade a tese central, a estrutura argumentativa, os fundamentos bíblicos, os riscos interpretativos e os elementos necessários para a futura elaboração de um sermão doutrinariamente sólido, hermeneuticamente coerente e pastoralmente equilibrado.

DIRETRIZES OBRIGATÓRIAS:
- Ser fiel ao conteúdo e à ordem lógica do artigo.
- Não inventar citações, fontes, páginas ou referências externas.
- Não transformar o texto em sermão.
- Não usar tom devocional, apelativo ou emocional.
- Não usar linguagem agressiva, sensacionalista ou caricatural.
- Manter sobriedade técnica, clareza e precisão.
- Considerar a moldura hermenêutica adventista historicista quando isso estiver claramente sustentado pelo próprio artigo.
- Preservar a coerência temática com a perspectiva do grande conflito, sem forçar essa linguagem se o artigo não a desenvolver explicitamente.
- Caso haja pontos ambíguos no artigo, apontá-los com cautela, sem preencher lacunas com invenções.

ESTRUTURA OBRIGATÓRIA DO RELATÓRIO:

1) Identificação do Artigo
- Título do artigo.
- Tema central em uma frase.
- Indicar se o artigo parece expositivo, doutrinário, histórico-profético, apologético ou misto.

2) Tese Central
- Explicar com clareza qual é a principal afirmação defendida pelo autor.
- Mostrar qual é o eixo interpretativo que sustenta essa tese.

3) Fundamentos Bíblicos Principais
- Listar os principais textos bíblicos usados ou pressupostos no artigo.
- Explicar a função de cada texto dentro do argumento.
- Indicar qual texto parece mais central para a futura pregação.

4) Linha Argumentativa do Artigo
- Organizar o raciocínio em 3 a 5 blocos lógicos.
- Para cada bloco, apresentar:
  a) ideia principal;
  b) base bíblica associada, se houver;
  c) contribuição do bloco para a tese central.

5) Eixo Hermenêutico e Exegético
- Explicar qual é a lógica interpretativa predominante no artigo.
- Indicar como o autor lida com símbolos, história, profecia, doutrina ou aplicação.
- Registrar, com sobriedade, a relação do artigo com a moldura do conflito entre Cristo e Satanás, se isso estiver presente no texto.

6) Núcleo Doutrinário a Preservar no Sermão
- Listar os pontos que não podem ser perdidos na futura transformação em sermão.
- Mostrar o que é essencial e o que é secundário.

7) Riscos Interpretativos ou Pastorais
- Apontar onde o leitor/ouvinte poderia confundir símbolos, etapas, aplicações ou conclusões.
- Indicar eventuais riscos de simplificação, exagero ou leitura apressada.
- Se não houver riscos relevantes, dizer isso explicitamente.

8) Base Preparatória para o Sermão
Apresentar:
- um título significativo sugerido para o sermão;
- um verso-chave sugerido para aparecer logo abaixo do título;
- o texto bíblico central sugerido para leitura;
- uma sugestão breve de oração antes da leitura do texto bíblico central;
- o tom predominante recomendado para o sermão;
- o tipo de fechamento recomendado.

9) Diretrizes para a Redação do Sermão
- Escrever instruções curtas e objetivas para a futura geração do sermão.
- Incluir:
  - preservar a tese central;
  - manter a ordem lógica do artigo;
  - evitar invenções;
  - evitar conclusões abruptas;
  - conduzir o encerramento de modo progressivo e coerente;
  - manter fidelidade bíblica, doutrinária e argumentativa.

IMPORTANTE:
- Não produzir o sermão agora.
- Não fazer apelo evangelístico final.
- Não criar subdivisões excessivas.
- Não citar Ellen G. White literalmente se isso não estiver no texto-fonte.
- Não extrapolar além do que o artigo sustenta.

TEXTO-FONTE:
{text}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--esboco", default="")
    ap.add_argument("--model", default="gpt-5")
    ap.add_argument("--max-chars", type=int, default=60000)
    args = ap.parse_args()

    docx = Path(args.docx)
    esboco = Path(args.esboco).resolve() if args.esboco else default_esboco_path()
    outdir = resolve_series_outdir(docx, Path(args.outdir), esboco)
    outdir.mkdir(parents=True, exist_ok=True)

    text = read_docx_text(docx)
    text = text[: args.max_chars]

    client = OpenAI()
    prompt = build_prompt_relatorio(text)
    resp = client.responses.create(model=args.model, input=prompt)

    base_name = canonical_base_stem(docx.stem)
    outpath = outdir / f"{base_name}__dossie.md"
    outpath.write_text(resp.output_text, encoding="utf-8")
    print(f"[OK] relatorio_tecnico: {outpath}")

if __name__ == "__main__":
    main()
