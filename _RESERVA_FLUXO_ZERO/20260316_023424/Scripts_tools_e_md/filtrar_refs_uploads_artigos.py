import csv
from collections import Counter

entrada = "referencias_arquivos_site.csv"
saida = "refs_uploads_artigos.csv"
saida_unicos = "refs_uploads_artigos_unicos.txt"

prefixo = "uploads/artigos/"

linhas = []
unicos = set()
por_campo = Counter()
por_model = Counter()

with open(entrada, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        path = (row.get("path") or "").strip()
        if path.startswith(prefixo):
            linhas.append(row)
            unicos.add(path)
            por_campo[row.get("field", "")] += 1
            por_model[f"{row.get('app','')}.{row.get('model','')}"] += 1

with open(saida, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["app", "model", "pk", "field", "path"],
        delimiter=";"
    )
    writer.writeheader()
    writer.writerows(linhas)

with open(saida_unicos, "w", encoding="utf-8") as f:
    for path in sorted(unicos):
        f.write(path + "\n")

print(f"Linhas filtradas ({prefixo}): {len(linhas)}")
print(f"Caminhos únicos ({prefixo}): {len(unicos)}")
print(f"CSV filtrado: {saida}")
print(f"Lista única: {saida_unicos}")

print("\nPor campo:")
for k, v in por_campo.most_common():
    print(f"  {k}: {v}")

print("\nPor model:")
for k, v in por_model.most_common():
    print(f"  {k}: {v}")