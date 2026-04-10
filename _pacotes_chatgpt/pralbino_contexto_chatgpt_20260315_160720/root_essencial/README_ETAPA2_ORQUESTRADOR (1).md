# Etapa 2 — Orquestrador de Sermões (Rodada 2)

Esta rodada aprofunda duas frentes do MVP anterior:

1. **Manifest mais rico antes do browse**
2. **Browse com seleção cumulativa e ajuste individual real**

## O que mudou nesta rodada

### 1) Manifest hidratado antes do browse
O `sermoes_inventory.py` agora:

- extrai um **título humano** melhor da `id_base`
  - ex.: `GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5`
  - vira `GOGUE E MAGOGUE`
- registra a **fonte** de cada metadado principal:
  - `fonte_titulo`
  - `fonte_serie`
  - `fonte_autor`
- preserva e reaproveita os metadados do manifest anterior
- aceita um arquivo opcional de **overrides** para corrigir metadados sem editar o código
- registra observações úteis no manifest, como:
  - faltas de artefatos essenciais
  - duplicidade
  - entrada alterada desde a última execução

### 2) Browse com seleção realmente operacional
O `sermoes_browse.py` agora:

- mantém a seleção mesmo quando você muda filtros ou reordena a tabela
- permite operações cumulativas:
  - **Selecionar visíveis**
  - **Desmarcar visíveis**
  - **Inverter visíveis**
  - **Limpar seleção**
- mostra resumo com:
  - total de itens
  - visíveis
  - selecionados totais
  - selecionados visíveis
- exibe melhor os metadados:
  - slug previsto
  - fonte do título/série/autor
  - observações do manifest

## Arquivos do patch

Copiar para:

```text
scripts/publicacao/
```

Arquivos:

- `sermoes_inventory.py`
- `sermoes_browse.py`
- `orquestrador_sermoes.py`

Os demais arquivos da rodada anterior podem continuar no lugar.

## Novo recurso: overrides de manifest

Por padrão, o orquestrador procura este arquivo opcional:

```text
Apenas_Local/manifests/manifest_sermoes_overrides.csv
```

Você também pode passar outro caminho com:

```text
--manifest-overrides "C:\caminho\manifest_sermoes_overrides.csv"
```

### Estrutura mínima do CSV de overrides

Campos típicos:

```csv
id_base,titulo,serie,autor,slug_previsto,observacoes
GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5,GOGUE E MAGOGUE,O GRANDE CONFLITO,Pr. Albino Marks,gogue-e-magogue,Título e série confirmados manualmente
```

Você só precisa preencher as colunas que deseja corrigir.

## Comando seguro para regenerar manifest + browse

Na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\SERMOES_FORMATADOS" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```

## O que observar no browse

1. Se os títulos ficaram mais humanos
2. Se série/autor vieram melhor preenchidos
3. Se a seleção continua marcada ao aplicar filtros
4. Se funciona a lógica:
   - filtrar por grupo
   - depois ajustar manualmente item por item
5. Se o resumo de selecionados muda corretamente

## Estado operacional (`status_execucao`)

O campo continua com a mesma lógica de governança do lote:

- `PENDENTE`
- `DRY_RUN`
- `OK_NEW`
- `OK_UPDATED`
- `SKIP_ALREADY_PUBLISHED`
- `SKIP_INCOMPLETE`
- `SKIP_UNCHANGED`
- `ERROR`

Ele serve para o browse e para o runner, permitindo filtros como:

- só pendentes
- só erros
- só simulações (`DRY_RUN`)
- só atualizados

## Próxima etapa natural após esta rodada

Depois de validar manifest + browse:

1. encaixar melhor os metadados já conhecidos nas etapas anteriores
2. testar `DryRun` com seleção exportada do browse
3. atualizar o manifest durante a execução real
4. refinar o runner com base no comportamento do pipeline completo
