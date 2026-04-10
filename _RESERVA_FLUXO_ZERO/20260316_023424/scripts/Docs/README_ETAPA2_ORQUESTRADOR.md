# Etapa 2 — Patch inicial do orquestrador de sermões

Este patch entrega um **MVP funcional** do orquestrador da Etapa 2, sem mexer na lógica interna do pipeline unitário da Etapa 1.

## Arquivos

- `scripts/publicacao/orquestrador_sermoes.py`
- `scripts/publicacao/sermoes_inventory.py`
- `scripts/publicacao/sermoes_browse.py`
- `scripts/publicacao/sermoes_runner.py`
- `scripts/publicacao/run_orquestrador_sermoes.ps1`

## O que já faz

1. varre uma pasta-base de sermões formatados;
2. agrupa por `id_base` usando os sufixos:
   - `__A4.html`
   - `__A5.html`
   - `__tablet.html`
   - `__A4.docx`
   - `__A4.pdf`
   - `__A5.pdf`
   - `__tablet.pdf`
3. monta `manifest_sermoes.csv` e `manifest_sermoes.json`;
4. detecta `COMPLETO`, `INCOMPLETO` e `DUPLICADO`;
5. gera um browse HTML local com:
   - busca
   - filtros
   - ordenação por coluna
   - seleção múltipla
   - download da seleção em JSON
6. executa em lote com:
   - filtros por série / autor / pasta / status / texto
   - `--dry-run`
   - `--limit`
   - `--continue-on-error`
   - `--skip-if-exists`
   - `--only-changed`
   - `--retry-failed`
7. grava log e relatório CSV.

## O que você precisa adaptar

Como o zip que eu recebi **não contém o app `sermoes` nem o pipeline final real da Etapa 1**, deixei a execução do lote flexível.

Você pode usar de dois jeitos:

### 1) Modo simples — apontar o script unitário

Se o seu pipeline final aceitar argumentos parecidos com os já documentados (`--titulo`, `--serie`, `--html-a4`, etc.), use:

```powershell
.\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -Execute `
  -UnitScript "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\scripts\publicacao\pipeline_publicar_sermao.py"
```

### 2) Modo exato — informar um template de comando

Esse é o melhor caminho quando o pipeline final já existe e você quer encaixar o orquestrador sem reescrever nada.

Exemplo:

```powershell
$tpl = 'powershell -ExecutionPolicy Bypass -File "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\scripts\publicacao\run_pipeline_sermao_completo.ps1" --titulo "{titulo}" --serie "{serie}" --html-a4 "{html_a4_path}" --html-a5 "{html_a5_path}" --html-tablet "{html_tablet_path}" --docx-a4 "{docx_a4_path}"'

.\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -DryRun `
  -Serie "Serie_02 - APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO" `
  -RunnerTemplate $tpl
```

## Comandos recomendados para começar

### 1. Só inventário + browse

```powershell
.\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```

### 2. Dry run com filtro e limite

```powershell
.\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -DryRun `
  -Limit 2 `
  -Search "GOGUE"
```

### 3. Rodar só os com erro anterior

```powershell
.\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -Execute `
  -RetryFailed `
  -ContinueOnError `
  -UnitScript "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\scripts\publicacao\pipeline_publicar_sermao.py"
```

## Limites desta primeira entrega

- ainda não cruza estado real do banco Django para preencher `registro_existe` / `publicado` automaticamente;
- ainda não lê seleção de volta do browse por upload automático — o HTML baixa o JSON, e esse JSON entra depois via `-SelectionFile`;
- a dedução de `serie` e `autor` é heurística e talvez precise de ajuste à sua árvore real;
- para a execução real do lote, talvez você precise acertar o `RunnerTemplate` uma vez só conforme a assinatura exata do pipeline da Etapa 1.

## Próxima volta recomendada

1. encaixar a assinatura exata do `run_pipeline_sermao_completo.ps1`;
2. preencher `registro_existe/publicado` consultando o Django;
3. enriquecer os estados do manifest;
4. salvar seleção do browse diretamente em `Apenas_Local/selecoes`.
