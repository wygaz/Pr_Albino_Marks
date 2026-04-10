# Manual Operacional — 1 Página
## Pr. Albino Marks | Artigos, Sermões e PDFs

### 1) Objetivo
Transformar artigos já extraídos em **sermões preparados** e, ao final, em **PDFs prontos para revisão/publicação**, preservando:
- fidelidade ao texto-fonte;
- coerência com a compreensão doutrinária da IASD;
- abordagem historicista de interpretação profética;
- linguagem pastoral, clara e reverente.

---

### 2) Cenário atual
Quando os artigos **já estiverem extraídos** em um lote (ex.: `Apenas_Local\anexos_filtrados\2025-11-25`), **pular** a etapa de baixar anexos do e-mail.

Fluxo reduzido:
1. **Normalizar títulos** do lote.
2. **Consolidar a série**.
3. **Medir tamanho** dos artigos.
4. **Segmentar** apenas os longos.
5. **Gerar/preparar sermão** por artigo ou segmento.
6. **Revisar DOCX** do sermão.
7. **Converter para PDF**.
8. **Controlar tudo no manifesto/planilha**.

---

### 3) Scripts principais
- `normalizar_titulos_pasta.py` → normaliza nomes/títulos dos DOCX.
- `consolidar_serie_por_esboco.py` → monta a pasta da série.
- `listar_artigos_docx_paginas.py` → mede tamanho (páginas).
- `segmentar_docx_pralbino.py` → divide longos por subtítulos/tamanho.
- `converter_em_pdf_por_esboco.py` → converte DOCX da série em PDF.

---

### 4) Convenção de identificação
Usar identificação estável na planilha/manifestação:
- `SR01` = série
- `SR01-A001` = artigo
- `SR01-A001-S01` = segmento

Exemplo da série atual:
- `SR01` = **APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO**
- `SR01-A001` = **GOGUE E MAGOGUE**

> Observação: os nomes físicos dos arquivos podem permanecer como estão; a numeração pode entrar primeiro no **manifesto**, sem quebrar o pipeline existente.

---

### 5) Regra prática de segmentação
- **Curtos/médios**: tratar o artigo inteiro.
- **Longos**: segmentar por subtítulos.
- **Muito longos**: segmentar por subtítulos + tamanho.

Prioridade: começar pelos médios/curtos para consolidar padrão visual e revisão.

---

### 6) Estrutura mínima do sermão preparado
1. Título
2. Texto base
3. Introdução
4. Tópicos principais
5. Aplicações pastorais
6. Apelo final
7. Oração final

---

### 7) Controle mínimo no manifesto
- `serie_codigo`
- `serie_nome`
- `artigo_codigo`
- `segmento_codigo`
- `id_item`
- `titulo_original`
- `titulo_normalizado`
- `arquivo_fonte`
- `paginas_artigo`
- `segmentado`
- `titulos_normalizados`
- `sermao_docx_gerado`
- `pdf_convertido`
- `aprovado_pr_albino`
- `observacoes`

---

### 8) Sequência local recomendada (atual)
1. Rodar normalização do lote.
2. Consolidar a série `APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO`.
3. Medir páginas.
4. Começar por `GOGUE E MAGOGUE`.
5. Gerar sermão DOCX.
6. Revisar.
7. Converter em PDF.
8. Registrar no manifesto.

---

### 9) Regra de ouro
**Não perder rastreabilidade.**
Cada sermão deve poder ser ligado claramente ao:
- lote de origem,
- série,
- artigo/segmento,
- versão DOCX,
- versão PDF,
- status de aprovação.
