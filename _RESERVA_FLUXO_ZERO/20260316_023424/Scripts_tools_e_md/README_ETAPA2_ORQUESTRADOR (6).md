# Patch Versão 8 — Manifest mais vivo + cabeçalho fixo

## O que entrou

- manifest de **artigos sem sermão** agora registra campos de progresso:
  - `etapas_concluidas_inferidas`
  - `etapas_concluidas_texto`
  - `ultima_operacao_solicitada`
  - `historico_operacoes`
- heurística de **etapas concluídas** a partir dos insumos locais:
  - `md` -> etapa 3
  - `docx` -> etapa 4
  - `html` -> etapa 6
  - `pdf` -> etapa 7
- operação sugerida ficou mais fina:
  - com PDF local -> sugerir `8`
  - com HTML local -> sugerir `7-8`
  - com DOCX local -> sugerir `5-8`
- browse com **cabeçalho da tabela fixo** em área de rolagem própria
- toolbar também fica presa no topo do browse
- metadados dos artigos mostram:
  - etapa atual
  - etapas concluídas
  - operação sugerida
  - última operação solicitada
  - histórico

## Como aplicar

Extrair na raiz do projeto, substituindo os arquivos existentes.

## Como testar

```powershell
powershell -ExecutionPolicy Bypass -File .\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -InputDirArtigos "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERIES_CLASSIFICADAS" `
  -WorkspaceArtigos "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```
