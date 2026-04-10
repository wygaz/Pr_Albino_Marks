from pathlib import Path

db_file = "refs_uploads_artigos_unicos.txt"
s3_file = "s3_artigos_unicos.txt"

db = set(
    linha.strip() for linha in Path(db_file).read_text(encoding="utf-8").splitlines()
    if linha.strip()
)

s3 = set(
    linha.strip() for linha in Path(s3_file).read_text(encoding="utf-8").splitlines()
    if linha.strip()
)

referenciados = sorted(s3 & db)
orfaos_s3 = sorted(s3 - db)
faltando_no_s3 = sorted(db - s3)

Path("s3_referenciados.txt").write_text("\n".join(referenciados) + ("\n" if referenciados else ""), encoding="utf-8")
Path("s3_orfaos.txt").write_text("\n".join(orfaos_s3) + ("\n" if orfaos_s3 else ""), encoding="utf-8")
Path("db_ausentes_no_s3.txt").write_text("\n".join(faltando_no_s3) + ("\n" if faltando_no_s3 else ""), encoding="utf-8")

print(f"Referenciados no banco e presentes no S3: {len(referenciados)}")
print(f"Presentes no S3 e NÃO referenciados no banco (candidatos a órfãos): {len(orfaos_s3)}")
print(f"Referenciados no banco e AUSENTES no S3: {len(faltando_no_s3)}")

print("\nArquivos gerados:")
print("- s3_referenciados.txt")
print("- s3_orfaos.txt")
print("- db_ausentes_no_s3.txt")