from openai import OpenAI

client = OpenAI()

prompt = """
Gere um mini-sermão estruturado com:

TÍTULO
TEXTO BÍBLICO BASE
INTRODUÇÃO (1 parágrafo)
3 PONTOS PRINCIPAIS
CONCLUSÃO
APLICAÇÃO PRÁTICA

Tema: Fidelidade doutrinária em sermões.
Inclua pelo menos 2 referências bíblicas.
Seja claro, objetivo e com tom pastoral.
"""

response = client.responses.create(
    model="gpt-4o-mini",
    input=prompt
)

print(response.output_text)