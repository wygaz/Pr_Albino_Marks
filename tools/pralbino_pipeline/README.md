# Pipeline Pr. Albino (preparo → publicação)

Este pacote move os scripts de `Apenas_Local/anexos_filtrados/Scripts/` para dentro do repositório (ex.: `tools/pralbino_pipeline/`), mantendo **os dados** (lotes, séries, PDFs, imagens) fora do git, em `Apenas_Local/anexos_filtrados/` (no `.gitignore`).

## 1) Onde ficam os dados (fora do git)
Estrutura esperada em `Apenas_Local/anexos_filtrados/`:

- `YYYY-MM-DD/` (lotes baixados do e-mail)
- `SERIES/<NOME>/DOCX|PDF|IMG` (série consolidada)

> Os scripts agora recebem `--data-root` (DataRoot) para apontar para `anexos_filtrados`.

## 2) Um único comando (ponta a ponta)
Exemplo (LOCAL, sem imagens):

```powershell
$env:ENV_NAME = "local"
.\tools\pralbino_pipeline\run_pipeline_pralbino.ps1 -Ini "2026-02-01" -Fim "2026-02-13" -SkipPrompts
```

Com prompts e **geração de imagens** (com consumo):

```powershell
$env:ENV_NAME = "local"
.\tools\pralbino_pipeline\run_pipeline_pralbino.ps1 -Ini "2026-02-01" -Fim "2026-02-13" -GenerateImages
```

Rodar usando um lote já existente:

```powershell
$env:ENV_NAME = "local"
.\tools\pralbino_pipeline\run_pipeline_pralbino.ps1 -Lote "2026-02-13" -SkipDownload
```

## 3) Publicação (import_series)
Ao final, o script tenta rodar o comando Django:

- `python manage.py import_series ...`
- se não existir, cai para `python manage.py importar_serie ...`

Ele importa a série detectada (pela última consolidada ou pelo `.last_series.txt`).

## 4) Imagens: modo seguro (default)
`gerar_imagens_lote.py` agora tem `--run`.

- **Sem `--run`**: apenas lista os arquivos que geraria (zero consumo).
- **Com `--run`**: executa chamadas à API e grava em `SERIES/<serie>/IMG/`.

O orquestrador (`run_pipeline_pralbino.ps1`) só chama imagens quando você usa `-GenerateImages`.

## 5) Reset do BD local para UTF-8 (script separado, uma única vez)

```powershell
.\tools\db_reset_local_utf8.ps1
# depois
python manage.py migrate
```

> O script roda `tools/db_check.py` (se existir) e aborta se o HOST não parecer local.
