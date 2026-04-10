import argparse
import re
from pathlib import Path
from docx import Document
from openai import OpenAI


GC_AP17_BLOCK = """Conformidade com “O Grande Conflito” (Ellen G. White):
- Ler Apocalipse 17 em chave historicista e adventista, em harmonia com o quadro de Babilônia como sistema religioso apóstata e confuso, em aliança ilícita com os poderes da terra.
- Preservar a centralidade do conflito entre verdade e erro, autoridade divina e autoridade humana, mandamentos de Deus e imposições religiosas.
- Manter coerência com a compreensão adventista da atuação histórica e final do sistema papal, sem especulação sensacionalista e sem extrapolações não sustentadas pelo texto-fonte.
- Dar ênfase pastoral ao chamado de Deus para sair da confusão religiosa, permanecer fiel a Cristo, à Sua Palavra e à verdadeira adoração.
- O sermão deve ser fiel ao artigo-fonte, coerente com a IASD e em harmonia temática com “O Grande Conflito”, especialmente quanto a Babilônia, apostasia, união igreja-Estado, crise final e juízo divino.
"""


def read_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def pick_anchors(text: str, k: int = 6) -> list[str]:
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.replace("\n", " "))
    candidates = [s.strip() for s in sentences if 50 <= len(s.strip()) <= 180]
    if len(candidates) <= k:
        return candidates[:k]

    n = len(candidates)
    idxs = sorted(set([0, n // 5, (2 * n) // 5, (3 * n) // 5, (4 * n) // 5, n - 1]))
    anchors = [candidates[i] for i in idxs if i < n]

    i = 0
    while len(anchors) < k and i < n:
        s = candidates[i]
        if s not in anchors:
            anchors.append(s)
        i += 1
    return anchors[:k]


def build_prompt_iasd(text: str) -> str:
    anchors = pick_anchors(text, k=6)
    anchors_block = "\n".join([f"⛓️ {a}" for a in anchors])

    formato = """FORMATO OBRIGATÓRIO (SERMÃO 25 min)
1) Título
2) Texto base (referência)
3) Introdução
4) 3–5 pontos

REGRAS DOS PONTOS:
- Cada ponto deve conter:
  a) explicação
  b) uma âncora textual copiada literalmente do TEXTO-FONTE, iniciada por "⛓️ "
  c) 1 referência bíblica citada
- Ao longo do sermão, use pelo menos 6 âncoras literais no total.
- As âncoras devem aparecer visivelmente no corpo do sermão. Não basta apenas usar a ideia.

5) Aplicações (3–6 itens)
6) Apelo final
7) Oração final
8) Checklist honesto:
   [ ] Fiel ao texto-fonte
   [ ] Coerente com IASD
   [ ] Em harmonia temática com O Grande Conflito
   [ ] Sem especulação/datas
   [ ] Sem inglês
   [ ] 6+ âncoras ⛓️ visíveis no corpo

REVISÃO FINAL OBRIGATÓRIA:
- Revise antes de concluir.
- Elimine frases truncadas, palavras quebradas, trechos sem sentido, repetições e erros gramaticais.
- Não marque um item do checklist como cumprido se ele não tiver sido realmente cumprido.
"""

    return f"""IDIOMA: Português do Brasil. Proibido usar palavras ou expressões em inglês.

IDENTIDADE DOUTRINÁRIA (IASD)
Você deve permanecer estritamente dentro das diretrizes doutrinárias da Igreja Adventista do Sétimo Dia (IASD), com fidelidade bíblica e espírito cristocêntrico.
Regras:
- Não ensine ideias contrárias às crenças adventistas.
- Evite especulações e datas não sustentadas pelo texto.
- Mantenha o foco em Cristo, na Escritura e na mensagem profética com prudência e reverência.
- Se o texto-fonte não afirmar algo, não assuma.

Fidelidade ao texto-fonte (obrigatório)
- Baseie o conteúdo no TEXTO-FONTE abaixo.
- Use as âncoras fornecidas e outras frases do TEXTO-FONTE, quando necessário.
- Copie literalmente as âncoras usadas, preservando seu sentido.
- Textos bíblicos: use apenas os textos citados no TEXTO-FONTE, ou no máximo 2 complementos claramente identificados como COMPLEMENTO.
- Se algo for aplicação pastoral, rotule: (Aplicação pastoral).

{GC_AP17_BLOCK}

ÂNCORAS SUGERIDAS DO TEXTO-FONTE:
{anchors_block}

{formato}

TEXTO-FONTE:
{text}
"""


def build_revision_prompt(draft: str) -> str:
    return f"""Revise o sermão abaixo sem mudar sua linha doutrinária, sem alterar sua estrutura principal e sem enfraquecer sua fidelidade ao texto-fonte.

OBJETIVO DA REVISÃO:
- Corrigir gramática, concordância, digitação e fluidez.
- Eliminar palavras quebradas, frases truncadas e trechos sem sentido.
- Preservar e manter visíveis as âncoras iniciadas por "⛓️ ".
- Não remover conteúdo importante.
- Não introduzir doutrina nova.
- Manter coerência com IASD, leitura historicista e harmonia temática com O Grande Conflito.
- Manter o texto em Português do Brasil.

Entregue apenas a versão final revisada.

SERMÃO:
{draft}
"""


def gerar_um_docx(docx: Path, outdir: Path, client: OpenAI, model: str, max_chars: int) -> None:
    text = read_docx_text(docx)
    text = text[:max_chars]

    prompt = build_prompt_iasd(text)
    resp = client.responses.create(model=model, input=prompt)
    draft = resp.output_text

    rev_prompt = build_revision_prompt(draft)
    rev = client.responses.create(model=model, input=rev_prompt)
    final_text = rev.output_text

    outpath = outdir / f"{docx.stem}__sermao25__{model}.md"
    outpath.write_text(final_text, encoding="utf-8")
    print(f"[OK] sermao25: {outpath}")


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--docx", help="Arquivo DOCX único")
    src.add_argument("--indir", help="Pasta com arquivos DOCX")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--max-chars", type=int, default=60000, help="recorte do texto para caber bem e agilizar")
    ap.add_argument("--glob", default="*.docx", help='Padrão de busca no modo --indir (default: "*.docx")')
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    client = OpenAI()

    if args.docx:
        gerar_um_docx(
            docx=Path(args.docx),
            outdir=outdir,
            client=client,
            model=args.model,
            max_chars=args.max_chars,
        )
        return

    indir = Path(args.indir)
    files = sorted(indir.glob(args.glob))
    if not files:
        print(f"[ERRO] Nenhum arquivo encontrado em: {indir} com padrão {args.glob}")
        return

    print(f"[INFO] Arquivos encontrados: {len(files)}")
    for docx in files:
        try:
            gerar_um_docx(
                docx=docx,
                outdir=outdir,
                client=client,
                model=args.model,
                max_chars=args.max_chars,
            )
        except Exception as e:
            print(f"[ERRO] {docx.name}: {e}")


if __name__ == "__main__":
    main()