# Plano de saneamento scriptal — Fase 1 v2

Esta fase foi corrigida para **preservar explicitamente a base da Etapa 2**.

## Objetivo

Fazer uma limpeza responsável, removendo apenas ruído evidente, sem tocar no núcleo que servirá de base para a retomada da homologação da Etapa 2.

## Núcleo protegido da Etapa 2

Não entra em quarentena automática:

- `scripts/publicacao/**`
- arquivos `.ps1` e `.py` da raiz
- `README_ETAPA2*`
- patches ligados à Etapa 2
- `Apenas_Local/**`
- código Django/apps/migrations

## Vai para quarentena automática segura

Apenas artefatos temporários e diagnósticos:

- `_pacotes_chatgpt`
- `_sanitizados_preview`
- `_diagnosticos_segredos`
- `_inventario_scripts`
- `_inventario_duplicatas`
- `A_Lei_no_NT/Zip/_temp_update`

## Relatórios gerados

A fase v2 gera:

- `nucleo_protegido_etapa2.txt`
- `arquivos_zero_bytes.txt`
- `notas_fase1_v2.txt`

## Por que esta versão é mais segura

Porque incorpora o contexto histórico confirmado:

- `scripts/publicacao` contém os scripts mais recentes testados da Etapa 2;
- os `.ps1` e `.py` da raiz também fazem parte do mesmo núcleo;
- os `README_ETAPA2*` e patches são documentação de avanço, não ruído;
- o problema da pausa anterior foi excesso de coleta em `Apenas_Local/anexos_filtrados`, não falta de maturidade do eixo técnico.

## Uso

### Prévia

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\sanear_workspace_pralbino_fase1_v2.ps1 -DryRun
```

### Execução real

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\sanear_workspace_pralbino_fase1_v2.ps1
```

## Próximo passo depois da Fase 1 v2

Retomar a classificação de duplicatas e eleger, com critério preservacionista:

- canônicos da raiz
- canônicos de `scripts/publicacao`
- canônicos de `tools/pralbino_pipeline`
- redundâncias reais que podem ir para quarentena
