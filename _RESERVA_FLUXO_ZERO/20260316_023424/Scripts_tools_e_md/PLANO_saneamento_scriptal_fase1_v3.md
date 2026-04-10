# Plano de saneamento scriptal — Fase 1 v3

Correção da v2: ajuste no filtro de auditoria de arquivos zerados.

## O que foi corrigido

Na v2, o filtro de exclusão de diretórios no bloco de auditoria de arquivos com 0 bytes
tratava caminhos de exclusão como se fossem objetos com `.FullName`, o que gerava erro.

Na v3, a checagem foi reescrita de forma explícita, comparando o caminho completo do arquivo
com cada diretório de exclusão.

## Uso

### Prévia

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\sanear_workspace_pralbino_fase1_v3.ps1 -DryRun
```

### Execução real

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\sanear_workspace_pralbino_fase1_v3.ps1
```

## Escopo preservado

- `scripts/publicacao/**`
- arquivos `.ps1` e `.py` da raiz
- `README_ETAPA2*`
- patches ligados à Etapa 2
- `Apenas_Local/**`
- código Django/apps/migrations

## Quarentena automática segura

- `_pacotes_chatgpt`
- `_sanitizados_preview`
- `_diagnosticos_segredos`
- `_inventario_scripts`
- `_inventario_duplicatas`
- `A_Lei_no_NT/Zip/_temp_update`
