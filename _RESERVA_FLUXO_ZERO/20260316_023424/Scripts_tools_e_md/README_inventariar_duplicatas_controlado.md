# Inventário controlado de duplicatas

Este script ajuda a comparar arquivos duplicados pelo **mesmo nome**, reunindo:

- caminho relativo
- hash SHA-256
- tamanho
- data de modificação
- status no Git (tracked / modified)
- classe sugerida
- candidato canônico

## Uso

Diagnóstico completo:

```powershell
python .\inventariar_duplicatas_controlado.py --root .
```

Somente grupos divergentes:

```powershell
python .\inventariar_duplicatas_controlado.py --root . --only-divergent
```

## Saída

O script gera uma pasta em:

```text
_inventario_duplicatas\<timestamp>
```

Com os arquivos:

- `inventario_duplicatas.csv`
- `inventario_duplicatas.md`

## Como ler

- **idêntico**: mesmo nome e mesmo hash
- **divergente**: mesmo nome e hash diferente
- **candidato canônico**: melhor palpite baseado em Git + caminho + sinais de maturidade + data/tamanho

## Observação

A decisão final continua sendo humana. O objetivo é tirar o processo do “olhômetro” e tornar a comparação auditável.
