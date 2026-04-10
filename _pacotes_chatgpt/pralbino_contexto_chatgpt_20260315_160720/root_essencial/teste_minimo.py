from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o-mini",
    input="Escreva um parágrafo curto sobre fidelidade doutrinária em sermões."
)

print(response.output_text)