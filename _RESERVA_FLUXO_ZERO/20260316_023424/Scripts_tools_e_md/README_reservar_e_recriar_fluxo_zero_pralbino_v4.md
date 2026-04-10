# Script — reserva geral + recriação do fluxo zero do Pr. Albino (v4)

A v4 corrige os dois pontos mais sensíveis da v3:

- não seleciona arquivo zerado para voltar ao workspace;
- força `README_ETAPA2_ORQUESTRADOR.md` da raiz como canônico.

Além disso, a v4 exclui alguns auxiliares que não são do fluxo imediato de reconstrução:
- `comparar_modelos_sermoes_pralbino.py`
- `exportar_formatos_sermao_md.py`
- `normalizar_s3_listagem.py`
- `sermoes_browse - .py`

## Uso

### Prévia

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v4.ps1 -DryRun
```

### Execução real

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v4.ps1 -Executar -Confirmacao RESERVAR_E_RECRIAR_FLUXO_ZERO
```
