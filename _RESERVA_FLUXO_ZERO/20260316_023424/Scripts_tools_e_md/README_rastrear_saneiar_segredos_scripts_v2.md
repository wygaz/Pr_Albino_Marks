# rastrear_saneiar_segredos_scripts_v2.py

Versão refinada do scanner de segredos hardcoded.

## O que mudou na v2
- ignora comentários Python
- ignora strings/docstrings Python
- evita falso positivo em casos como:
  - `os.getenv("DATABASE_URL")`
  - `print("DATABASE_URL =", ...)`
  - linhas comentadas com nomes de variáveis de ambiente
- em PowerShell, ignora linhas comentadas iniciadas com `#`

## Uso

Diagnóstico:
```powershell
python .\rastrear_saneiar_segredos_scripts_v2.py --root .
```

Preview seguro:
```powershell
python .\rastrear_saneiar_segredos_scripts_v2.py --root . --apply-preview
```

Aplicação real:
```powershell
python .\rastrear_saneiar_segredos_scripts_v2.py --root . --apply-inplace
```

## Recomendação
Rode primeiro só em diagnóstico. Depois use `--apply-preview`. Só aplique `--apply-inplace` após conferir o relatório e os arquivos preview.
