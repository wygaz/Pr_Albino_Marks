# Script — reserva geral + recriação do fluxo zero do Pr. Albino (v2)

Correção principal da v2:
- no `-DryRun`, agora a fase de seleção já mostra os arquivos que seriam copiados de volta para `Apenas_Local\anexos_filtrados`.

## O que ele faz

- move para reserva as zonas operacionais espalhadas;
- recria `Apenas_Local` enxuto;
- devolve para `Apenas_Local\anexos_filtrados` apenas arquivos do fluxo zero:
  extração, geração e publicação de artigos e sermões.

## Alvos movidos para a reserva

- `Apenas_Local`
- `scripts`
- `tools\Scripts`
- `tools\pralbino_pipeline`
- `tools\pralbino_sermoes`
- `A_Lei_no_NT\Zip`
- arquivos operacionais soltos da raiz

## Protegido / não tocado

- apps Django
- `manage.py`
- `.git`
- `venv` / `.venv`
- banco
- `media`
- `static`

## Uso

### Prévia

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v2.ps1 -DryRun
```

### Execução real

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\reservar_e_recriar_fluxo_zero_pralbino_v2.ps1 -Executar -Confirmacao RESERVAR_E_RECRIAR_FLUXO_ZERO
```
