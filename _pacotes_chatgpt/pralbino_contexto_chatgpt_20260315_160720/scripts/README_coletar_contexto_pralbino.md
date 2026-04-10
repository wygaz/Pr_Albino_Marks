# Script para juntar o que importa do Pr_Albino_Marks

Arquivo principal:
- `coletar_contexto_pralbino_para_chatgpt.ps1`

## O que ele junta por padrão
- arquivos essenciais da raiz (`manage.py`, `requirements*.txt`, `Procfile`, `railway.json`, `README*`, `*.md`, `*.ps1`, `*.py`, etc.)
- diretórios do app, se existirem: `pralbinomarks`, `artigos`, `apps`, `templates`, `scripts`, `docs`, `requirements`
- `static` customizado, excluindo `static/admin`
- scripts espalhados em:
  - `Apenas_Local/scripts`
  - `Apenas_Local/Scripts`
  - `Apenas_Local/anexos_filtrados/scripts`
  - `Apenas_Local/anexos_filtrados/Scripts`
  - `Apenas_Local/anexos_filtrados/sermoes/producao`
- contexto operacional leve:
  - `Apenas_Local/manifests`
  - `Apenas_Local/browse`
  - `Apenas_Local/RELATORIOS_TECNICOS`
  - `Apenas_Local/SERMOES_GERADOS`
  - `Apenas_Local/SERMOES_FORMATADOS`
- contexto de homologação:
  - `Apenas_Local/anexos_filtrados/ESBOCOS_FILTRADOS`
  - `Apenas_Local/anexos_filtrados/IMG`

## O que ele exclui automaticamente
- `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, caches
- `*.pyc`, `*.pyo`, `*.log`, `*.tmp`, `*.bak`, `*.sqlite3`, `*.db`
- `static/admin`

## Opcionais
- `-IncludeWorkspacePesado` => inclui `Apenas_Local/anexos_filtrados/SERIES_CLASSIFICADAS`
- `-IncludeDownloadsReferenciados` => inclui `Apenas_Local/downloads_referenciados`
- `-IncludeMedia` => inclui `media`
- `-DryRun` => só simula

## Exemplo de uso
```powershell
cd C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado
powershell -ExecutionPolicy Bypass -File .\coletar_contexto_pralbino_para_chatgpt.ps1
```

## Exemplo mais completo
```powershell
powershell -ExecutionPolicy Bypass -File .\coletar_contexto_pralbino_para_chatgpt.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -IncludeWorkspacePesado `
  -IncludeDownloadsReferenciados
```

## Dry run
```powershell
powershell -ExecutionPolicy Bypass -File .\coletar_contexto_pralbino_para_chatgpt.ps1 -DryRun
```
