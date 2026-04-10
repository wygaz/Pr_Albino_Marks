# Etapa 2 — Orquestrador de Sermões — Rodada 7

Esta rodada abre o próximo passo do painel operacional:

- **dois diretórios de entrada distintos**
  - `InputDir` = sermões formatados
  - `InputDirArtigos` = artigos/insumos para geração
- **WorkspaceArtigos** opcional para rastrear insumos locais dos artigos
- contexto **Artigos sem sermão** agora pode ser alimentado pelo **BD + arquivos locais**
- novo campo **Operação (artigos)** no browse
  - aceita `5`
  - aceita `3-7`
  - aceita `1,5,6,7,8`
  - aceita combinações como `1-3,5,8`
- exportação JSON da seleção passa a levar:
  - `current_context`
  - `operation_spec`
  - `operation_plan`
  - `browse_meta`

## Legenda 1–9

1. Baixar anexos do e-mail  
2. Normalizar  
3. Consolidar  
4. Gerar DOCX base  
5. Gerar sermão  
6. Gerar HTMLs  
7. Gerar PDFs  
8. Publicar  
9. Pipeline completo

## Arquivos deste patch

- `scripts/publicacao/orquestrador_sermoes.py`
- `scripts/publicacao/sermoes_browse.py`
- `scripts/publicacao/artigos_django.py`
- `scripts/publicacao/pipeline_steps.py`
- `scripts/publicacao/run_orquestrador_sermoes.ps1`

## Uso — browse com dois diretórios

Estando em `scripts\publicacao`:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS" `
  -InputDirArtigos "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\ARTIGOS" `
  -WorkspaceArtigos "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```

> Ajuste `InputDirArtigos` para a pasta real onde ficam os insumos dos artigos no seu projeto.

## O que mudou no contexto “Artigos sem sermão”

Agora ele pode mostrar pendências vindas de duas fontes:

1. **Artigos do BD** ainda não cobertos pelos sermões encontrados
2. **Arquivos locais** encontrados em `InputDirArtigos`, mesmo quando ainda não houver correspondência perfeita com o BD

Cada linha de artigo pode carregar:

- `etapa_atual`
- `operacao_recomendada`
- caminhos locais (`workspace_docx_path`, `workspace_html_path`, `workspace_pdf_path`)
- `workspace_source_types`

## Exportação JSON

Ao baixar a seleção no contexto de artigos, o JSON passa a trazer também o plano interpretado:

```json
{
  "current_context": "artigos_sem_sermao",
  "selected_ids": ["artigo__123"],
  "operation_spec": "3-7",
  "operation_plan": {
    "normalized": "3,4,5,6,7",
    "steps": [3,4,5,6,7],
    "labels": [
      "3. Consolidar",
      "4. Gerar DOCX base",
      "5. Gerar sermão",
      "6. Gerar HTMLs",
      "7. Gerar PDFs"
    ],
    "valid": true,
    "error": ""
  }
}
```

## Observação importante

Nesta rodada, o painel já **capta e exporta** o plano de operações para os artigos.
A execução em lote desse plano ainda será ligada na próxima continuidade.
