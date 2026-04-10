# Etapa 2 — Rodada 6

Ajustes desta rodada:

1. **Chaveador funcional de contexto no browse**
   - `Sermões formatados`
   - `Artigos sem sermão`
   - a troca é feita no topo da interface, sem pop-up.

2. **Contexto `Artigos sem sermão`**
   - consulta o BD Django (`Artigo`)
   - compara com os sermões já encontrados
   - mostra os artigos que ainda não viraram sermão

3. **Seleção independente por contexto**
   - a seleção do browse é mantida separadamente para cada contexto
   - o JSON exportado agora inclui `current_context`

4. **Manifest de artigos pendentes**
   - `Apenas_Local/manifests/manifest_artigos_sem_sermao.csv`
   - `Apenas_Local/manifests/manifest_artigos_sem_sermao.json`

5. **Visual do browse ajustado por contexto**
   - no contexto artigos, a coluna `Publicado` vira `Visível`
   - a coluna `Completo` vira `Sermão`
   - a coluna `Artefatos` vira `Ação`
   - a ação sugerida aparece como `GERAR`

## Observação importante

Nesta rodada, o contexto `Artigos sem sermão` já é **funcional para navegação, filtro e seleção**.
A execução de geração em lote a partir desse contexto será a próxima continuidade.

## Arquivos novos/atualizados

- `scripts/publicacao/artigos_django.py`
- `scripts/publicacao/orquestrador_sermoes.py`
- `scripts/publicacao/sermoes_browse.py`
- `scripts/publicacao/run_orquestrador_sermoes.ps1`

## Aplicação

Extraia na raiz do projeto, substituindo os arquivos existentes.
