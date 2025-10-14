import subprocess
import re
import sys
import os

# Padrões de chaves sensíveis
PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"aws_secret_access_key\s*=\s*[\'\"]?.+[\'\"]?",
    "AWS Bucket Name": r"AWS_STORAGE_BUCKET_NAME\s*=\s*[\'\"]?.+[\'\"]?",
    "Django SECRET_KEY": r"SECRET_KEY\s*=\s*[\'\"]?.+[\'\"]?",
    "DATABASE_URL": r"DATABASE_URL\s*=\s*[\'\"]?.+[\'\"]?",
}

def get_tracked_files():
    """Retorna arquivos versionados e não ignorados."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip().split("\n")

def check_files(files):
    """Verifica os arquivos em busca de padrões sensíveis."""
    problems = []

    for filepath in files:
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                for label, pattern in PATTERNS.items():
                    if re.search(pattern, content):
                        problems.append((filepath, label))
        except (UnicodeDecodeError, FileNotFoundError):
            continue  # ignora arquivos binários ou problemáticos

    return problems

def main():
    print("🔐 Verificando arquivos versionados e não ignorados...\n")
    files = get_tracked_files()
    problems = check_files(files)

    if problems:
        print("🚨 Vazamentos encontrados:")
        for filepath, label in problems:
            print(f" - {label} em {filepath}")
        print("\n❌ Corrija antes de fazer commit/push.\n")
        sys.exit(1)
    else:
        print("✅ Nenhuma chave sensível detectada em arquivos rastreados.\n")

if __name__ == "__main__":
    main()

print("\n✅ Nenhuma chave sensível detectada em arquivos rastreados.")
print("🟢 Projeto seguro para commit e deploy.\n")