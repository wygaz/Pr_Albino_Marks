import argparse
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
    ap.add_argument("--model", default="gpt-5")
    ap.add_argument("--max-chars", type=int, default=60000)
    args = ap.parse_args()

    docx = Path(args.docx)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    text = read_docx_text(docx)
    text = text[: args.max_chars]

    client = OpenAI()
    prompt = build_prompt_relatorio(text)
    resp = client.responses.create(model=args.model, input=prompt)

    outpath = outdir / f"{docx.stem}__relatorio_tecnico__{args.model}.md"
    outpath.write_text(resp.output_text, encoding="utf-8")
    print(f"[OK] relatorio_tecnico: {outpath}")

if __name__ == "__main__":
    main()