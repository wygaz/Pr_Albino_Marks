import argparse
import re
from pathlib import Path
from docx import Document
from openai import OpenAI

def read_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)

def pick_anchors(text: str, k: int = 6) -> list[str]:
    # Heurística simples: pega frases “boas” (não muito curtas/nem enormes) do início/meio/fim
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.replace("\n", " "))
    candidates = [s.strip() for s in sentences if 50 <= len(s.strip()) <= 160]
    if len(candidates) <= k:
        return candidates[:k]

    n = len(candidates)
    idxs = sorted(set([0, n//4, n//2, (3*n)//4, n-1]))
    anchors = [candidates[i] for i in idxs if i < n]

    # completa até k
    i = 0
    while len(anchors) < k and i < n:
        s = candidates[i]
        if s not in anchors:
            anchors.append(s)
        i += 1
    return anchors[:k]

def build_prompt_iasd(text: str, mode: str) -> str:
    anchors = pick_anchors(text, k=6)
    anchors_block = "\n".join([f"⛓️ {a}" for a in anchors])

    if mode == "sermonete":
        formato = """FORMATO (SERMONETE 15 min)
1) Título
2) Texto base (referência)
3) Introdução (curta)
4) 2–3 pontos (cada ponto com: explicação + ⛓️ + 1 referência bíblica citada)
5) Aplicações (2–4 itens)
6) Apelo final (curto)
7) Oração final (curta)
8) Checklist:
   [ ] Fiel ao texto-fonte
   [ ] Coerente com IASD
   [ ] Sem especulação/datas
   [ ] Sem inglês
   [ ] 6+ âncoras ⛓️
"""
    else:
        formato = """FORMATO (SERMÃO 25 min)
1) Título
2) Texto base (referência)
3) Introdução
4) 3–5 pontos (cada ponto com: explicação + ⛓️ + 1 referência bíblica citada)
5) Aplicações (3–6 itens)
6) Apelo final
7) Oração final
8) Checklist:
   [ ] Fiel ao texto-fonte
   [ ] Coerente com IASD
   [ ] Sem especulação/datas
   [ ] Sem inglês
   [ ] 6+ âncoras ⛓️
"""

    return f"""IDIOMA: Português do Brasil.

TAREFA:
Produzir um RELATÓRIO TEOLÓGICO TÉCNICO (não sermão) baseado no TEXTO-FONTE fornecido.

OBJETIVO:
Avaliar a coerência doutrinária, a consistência profética e a harmonia com a interpretação historicista adventista do período dos 1260 anos.

HERMENÊUTICA OBRIGATÓRIA:
- Princípio dia-ano.
- Daniel 7:25; Apocalipse 12:6,14; 13:5 como textos paralelos.
- Período 538–1798 como aplicação histórica tradicional.
- Supremacia papal medieval.
- Perseguição aos santos.
- Papel de Satanás como agente por trás do sistema.
- Harmonia conceitual com a abordagem apresentada em “O Grande Conflito”, de Ellen G. White (sem inventar citações ou páginas).

ESTRUTURA DO RELATÓRIO:

1) Resumo Teológico do Artigo
   - Síntese clara do argumento central.
   - Como o autor conecta os 1260 anos a Satanás.

2) Fundamentos Bíblicos Utilizados
   - Lista e explicação dos textos empregados.
   - Coerência entre Daniel e Apocalipse.
   - Avaliação do uso do princípio dia-ano.

3) Estrutura Argumentativa
   - Sequência lógica do raciocínio.
   - Pontos fortes.
   - Possíveis lacunas.

4) Conformidade com a Teologia Adventista
   - Está alinhado com a interpretação historicista?
   - Está coerente com “O Grande Conflito”?
   - Há risco de exagero ou simplificação?

5) Riscos Interpretativos Potenciais
   - Onde o leitor poderia interpretar mal?
   - Pontos que exigem cuidado pastoral.

IMPORTANTE:
- Linguagem técnica, sóbria e acadêmica.
- Não produzir apelo espiritual.
- Não transformar em sermão.
- Não usar inglês.
- Não inventar citações externas.

TEXTO-FONTE:
{TEXTO}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--max-chars", type=int, default=60000, help="recorte do texto para caber bem e agilizar")
    args = ap.parse_args()

    docx = Path(args.docx)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    text = read_docx_text(docx)
    text = text[: args.max_chars]

    client = OpenAI()

    for mode, suffix in [("sermao", "sermao25"), ("sermonete", "sermonete15")]:
        prompt = build_prompt_iasd(text, mode=mode)
        resp = client.responses.create(model=args.model, input=prompt)
        outpath = outdir / f"{docx.stem}__{suffix}__{args.model}.md"
        outpath.write_text(resp.output_text, encoding="utf-8")
        print(f"[OK] {suffix}: {outpath}")

if __name__ == "__main__":
    main()