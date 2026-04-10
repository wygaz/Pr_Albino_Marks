import argparse
from pathlib import Path
from openai import OpenAI


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    ap.add_argument("--model", default="gpt-5")
    args = ap.parse_args()

    relatorio_path = Path(args.relatorio)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    relatorio = read_text(relatorio_path)

    client = OpenAI()
    prompt = build_prompt_sermao(relatorio)
    resp = client.responses.create(model=args.model, input=prompt)

    outpath = outdir / f"{relatorio_path.stem}__sermao__{args.model}.md"
    outpath.write_text(resp.output_text, encoding="utf-8")
    print(f"[OK] sermao: {outpath}")


if __name__ == "__main__":
    main()