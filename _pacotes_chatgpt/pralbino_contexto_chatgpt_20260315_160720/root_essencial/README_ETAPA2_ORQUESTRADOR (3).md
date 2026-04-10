# Etapa 2 — Rodada 5

Ajustes desta rodada:

1. **Título limpo no browse**
   - `rotulo_curto` agora fica igual ao título visível por padrão.
   - O sufixo técnico da geração (`__5`, `relatorio_tecnico`, `gpt-5`) sai da interface.

2. **Nome sugerido para o arquivo final**
   - Novo campo no manifest: `nome_arquivo_canonico`
   - Heurística: `titulo-slug__sermao__5`
   - Ex.: `gogue-e-magogue__sermao__5`

3. **Match com BD mais inteligente**
   - tenta por slug direto
   - tenta por prefixo de slug
   - tenta por variantes normalizadas do título
   - usa `Série = área` e `Autor = autor` quando encontra o Artigo

4. **Browse**
   - não repete a segunda linha do título quando `rotulo_curto == titulo`
   - mostra `Nome sugerido` nos metadados

## Arquivos atualizados

- `scripts/publicacao/sermoes_inventory.py`
- `scripts/publicacao/sermoes_django.py`
- `scripts/publicacao/sermoes_browse.py`

## Aplicação

Extraia na raiz do projeto, substituindo os arquivos existentes.
