# Rastrear e sanear segredos em scripts

Este utilitário faz duas coisas:

1. **varre scripts** (`.py`, `.ps1`, `.psm1`, `.bat`, `.cmd`) em diretórios relevantes do projeto;
2. **detecta segredos hardcoded** por padrões conservadores e sugere/envia a substituição para variáveis de ambiente.

## O que ele procura

Principalmente:

- `password = "..."`
- `token = "..."`
- `api_key = "..."`
- `SECRET_KEY = "..."`
- `DATABASE_URL = "postgres://..."`
- kwargs Python como `password="..."`
- assigns PowerShell como `$password = "..."`

## O que ele NÃO faz por padrão

- não altera nada sem você pedir;
- não mexe em bucket/region/host/port/dbname/user por padrão, porque isso costuma ser **configuração** e nem sempre é segredo;
- não tenta reescrever Markdown, JSON, DOCX ou arquivos binários.

## Modos de uso

### 1) Diagnóstico puro

```powershell
python .\rastrear_saneiar_segredos_scripts.py --root .
```

Gera:

- `_diagnosticos_segredos\<timestamp>\relatorio_segredos.csv`
- `_diagnosticos_segredos\<timestamp>\relatorio_segredos.md`
- `_diagnosticos_segredos\<timestamp>\.env.segredos_template`

### 2) Preview seguro

```powershell
python .\rastrear_saneiar_segredos_scripts.py --root . --apply-preview
```

Cria cópias sanitizadas em:

- `_sanitizados_preview\...`

Sem tocar nos originais.

### 3) Aplicação in-place com backup

```powershell
python .\rastrear_saneiar_segredos_scripts.py --root . --apply-inplace
```

Antes de editar, ele salva backup em:

- `_backup_sanitizacao\<timestamp>\...`

## Diretórios já cobertos

- `.`
- `scripts`
- `Utilitarios`
- `Utilitarios/Scripts`
- `Apenas_Local/scripts`
- `Apenas_Local/anexos_filtrados/Scripts`
- `Apenas_Local/anexos_filtrados/sermoes/producao`

Você pode acrescentar outros com `--include-dir`.

## Como o script reescreve

### Python

De:

```python
password="novasenha123"
```

Para:

```python
password=os.getenv("DB_PASSWORD", "")
```

Se o arquivo Python não tiver `import os`, ele adiciona.

### PowerShell

De:

```powershell
$secretKey = "abc123"
```

Para:

```powershell
$secretKey = $env:SECRET_KEY
```

## Fluxo recomendado

1. Rodar **diagnóstico puro**.
2. Revisar `relatorio_segredos.md`.
3. Rodar **preview**.
4. Comparar os previews.
5. Só então usar `--apply-inplace`.

## Observação importante

Para o seu caso, vale separar em duas classes:

- **segredo real**: senha, token, chave, DSN com credencial;
- **configuração de infraestrutura**: bucket, região, host, dbname, username.

Este script já nasce conservador justamente para evitar “saneamento destrutivo”.
