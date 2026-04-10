from pathlib import Path

entrada = "s3_artigos_raw.txt"
saida = "s3_artigos_unicos.txt"

linhas = Path(entrada).read_text(encoding="utf-8").splitlines()
paths = []

for linha in linhas:
    linha = linha.strip()
    if not linha:
        continue

    # Formato típico:
    # 2026-03-10 03:00:00      12345 uploads/artigos/arquivo.docx
    partes = linha.split()
    if len(partes) >= 4:
        path = " ".join(partes[3:])
        if path.startswith("uploads/artigos/"):
            paths.append(path)

paths = sorted(set(paths))
Path(saida).write_text("\n".join(paths) + "\n", encoding="utf-8")

print(f"Total S3 únicos: {len(paths)}")
print(f"Arquivo gerado: {saida}")