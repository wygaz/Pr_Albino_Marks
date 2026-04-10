# Script — reserva geral + recriação do fluxo zero do Pr. Albino (v3)

Versão endurecida para a purificação do workspace.

## O que a v3 exclui do retorno ao workspace

- `__pycache__`
- `*.pyc`
- `_temp_update`
- `*.zip`
- `site.webmanifest`
- nomes com `(1)`, `(2)` etc.
- nomes com `Old_` / `_Old_`
- `README_ETAPA2_ORQUESTRADOR (n).md`
- `Apenas_Local\manifests\*`
- `Apenas_Local\browse\*`

## O que a v3 restaura para `Apenas_Local\anexos_filtrados`

Apenas:
- scripts `.py` e `.ps1` do fluxo zero
- `README_ETAPA2_ORQUESTRADOR.md`

## Como a v3 escolhe entre duplicatas

Agrupa por **nome de arquivo** e escolhe a melhor fonte por prioridade aproximada:

1. `tools\pralbino_pipeline`
2. `scripts\publicacao`
3. `tools\pralbino_sermoes`
4. `tools\Scripts`
5. `Apenas_Local\anexos_filtrados\Scripts`
6. raiz

## Uso

### Prévia

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v3.ps1 -DryRun
```

### Execução real

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v3.ps1 -Executar -Confirmacao RESERVAR_E_RECRIAR_FLUXO_ZERO
```
