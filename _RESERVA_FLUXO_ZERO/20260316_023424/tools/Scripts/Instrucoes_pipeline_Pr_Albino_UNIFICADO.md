# Instruções Unificadas — Pipeline Pr. Albino Marks

Este arquivo consolida a versão atual do pipeline do projeto **Pr. Albino Marks** em um único manual operacional.

Ele cobre:
- fluxo de **anexos / normalização / consolidação / PDFs / publicação / imagens**;
- fluxo novo de **relatório técnico → sermão → formatação final**;
- comandos prontos com parâmetros;
- função de cada script;
- observações práticas para a versão atual.

---

## 1) Escopo desta versão

### O que está fechado nesta versão
1. Baixar anexos do e-mail do Pr. Albino.
2. Normalizar nomes e título interno dos `.docx`.
3. Consolidar artigos por série com base em ESBOÇO.
4. Gerar PDFs dos artigos.
5. Importar série no projeto Django.
6. Gerar prompts de imagens e imagens em lote.
7. Gerar **relatório técnico** de um artigo em `.md`.
8. Gerar **sermão** a partir do relatório técnico em `.md`.
9. Exportar o sermão para:
   - `tablet.html`
   - `A4.html`
   - `A5.html`
   - `A4.docx`

### O que ficou para upgrade futuro
- pipeline interativo com modo seguro `[s/N]`;
- checklist com marcação por etapa;
- manifest enriquecido para controlar relatório técnico, sermão e formatação;
- orquestração mais modular por série / artigo / sermão.

---

## 2) Estrutura de pastas esperada

```text
Pr_Albino_Marks_restaurado/
  Apenas_Local/
    anexos_filtrados/
      Scripts/
        baixar_anexos_pralbino_final.py
        normalizar_titulos_pasta.py
        listar_artigos_docx_paginas.py
        segmentar_docx_pralbino.py
        consolidar_serie_por_esboco.py
        converter_em_pdf_por_esboco.py
        gerar_prompts_imagens.py
        gerar_imagens_lote.py
      YYYY-MM-DD/
      DOCX_NORMALIZADOS/
      SERIES/
      SERIES_CLASSIFICADAS/
    RELATORIOS_TECNICOS/
    SERMOES_GERADOS/
    SERMOES_FORMATADOS/
  gerar_relatorio_tecnico_de_docx.py
  gerar_sermao_de_relatorio.py
  exportar_formatos_sermao_md.py
```

### Significado das pastas principais
- `Scripts/`: scripts do pipeline clássico de artigos.
- `YYYY-MM-DD/`: lote bruto ou semibruto de anexos baixados por data.
- `DOCX_NORMALIZADOS/`: apoio para seleção e preparação de sermões.
- `SERIES/`: consolidação oficial por série para publicação.
- `SERIES_CLASSIFICADAS/`: pasta de apoio usada no fluxo atual de sermões por série.
- `RELATORIOS_TECNICOS/`: saída dos relatórios técnicos em `.md`.
- `SERMOES_GERADOS/`: saída dos sermões em `.md`.
- `SERMOES_FORMATADOS/`: saídas finais de leitura e impressão.

---

## 3) Pré-requisitos

### 3.1) Pacotes Python
No `venv` do projeto:

```powershell
pip install imapclient python-dotenv python-docx
```

### 3.2) LibreOffice
Usado para conversão em lote para PDF.

Se o caminho não for encontrado automaticamente, configurar no `.env.local`:

```env
SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

### 3.3) Chave da API (para relatório técnico, sermão e imagens)
Na sessão atual do PowerShell:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_AQUI"
```

Para conferir:

```powershell
$env:OPENAI_API_KEY
```

> Observação: essa variável vale para a janela atual do PowerShell. Se fechar a janela, será preciso definir de novo.

---

## 4) Configuração do `.env.local`

Criar ou editar, na raiz do projeto:

```env
EMAIL_USER=seuemail@gmail.com
EMAIL_PASS=SUA_SENHA_DE_APP_DE_16_CARACTERES
SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

### Observações
- `EMAIL_PASS` deve ser **senha de app do Google**, não a senha comum.
- `SOFFICE_PATH` é opcional, mas recomendado.

---

## 5) Fluxos operacionais

# 5A) Fluxo completo — quando ainda é preciso baixar anexos do e-mail

Entre na pasta dos scripts:

```powershell
cd "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts"
```

### Passo 1 — Baixar anexos

```powershell
python .\baixar_anexos_pralbino_final.py
```

### Exemplo com parâmetros

```powershell
python .\baixar_anexos_pralbino_final.py --ini 2026-01-01 --fim 2026-01-31
```

### Saídas esperadas
- criação de lote em `anexos_filtrados/YYYY-MM-DD/`;
- `.docx` renomeados;
- título interno atualizado;
- PDFs gerados, se escolhido;
- possível consolidação em série.

---

# 5B) Fluxo reduzido — quando os artigos já estão extraídos localmente

Use quando os `.docx` já estão no lote local.

### Passo 1 — Normalizar títulos do lote

```powershell
python .\normalizar_titulos_pasta.py --lote 2025-11-25
```

### Passo 2 — Consolidar a série

```powershell
python .\consolidar_serie_por_esboco.py
```

Ou forçando lote e série:

```powershell
python .\consolidar_serie_por_esboco.py --lote 2025-11-25 --series "NOME DA SÉRIE"
```

### Passo 3 — Converter a série em PDF

```powershell
python .\converter_em_pdf_por_esboco.py
```

Ou forçando a série:

```powershell
python .\converter_em_pdf_por_esboco.py --serie "NOME DA SÉRIE"
```

### Passo 4 — Importar no Django

Local:

```powershell
$env:ENV_NAME="local"
python manage.py importar_serie --serie "NOME DA SÉRIE"
```

Remoto, primeiro em teste:

```powershell
$env:ENV_NAME="remoto"
python manage.py importar_serie --serie "NOME DA SÉRIE" --dry-run --limit 3
python manage.py importar_serie --serie "NOME DA SÉRIE"
```

### Passo 5 — Gerar prompts de imagens

```powershell
python .\gerar_prompts_imagens.py
```

### Passo 6 — Gerar imagens em lote

Modo econômico:

```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\NOME DA SÉRIE"
```

Paisagem, ainda econômico:

```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\NOME DA SÉRIE" --size 1536x1024 --quality low
```

---

# 5C) Fluxo de sermões — versão atual fechada

## Objetivo
Transformar um artigo `.docx` em:
1. relatório técnico `.md`;
2. sermão `.md`;
3. saídas finais formatadas (`tablet.html`, `A4.html`, `A5.html`, `A4.docx`).

## Ordem atual do fluxo
1. localizar o artigo `.docx`;
2. gerar relatório técnico;
3. revisar o relatório técnico;
4. gerar sermão a partir do relatório;
5. revisar o sermão `.md`;
6. exportar os formatos finais.

### Exemplo real de artigo usado no piloto
```text
C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\SERIES_CLASSIFICADAS\Serie_02 - APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO\GOGUE E MAGOGUE.docx
```

---

## 6) Comandos prontos — relatório técnico, sermão e formatação

### 6.1) Gerar relatório técnico a partir de um artigo `.docx`

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_AQUI"

python .\gerar_relatorio_tecnico_de_docx.py `
  --docx "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\SERIES_CLASSIFICADAS\Serie_02 - APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO\GOGUE E MAGOGUE.docx" `
  --outdir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\RELATORIOS_TECNICOS" `
  --model "gpt-5" `
  --max-chars 60000
```

### Saída esperada
```text
C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\RELATORIOS_TECNICOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5.md
```

---

### 6.2) Gerar sermão a partir do relatório técnico

```powershell
python .\gerar_sermao_de_relatorio.py `
  --relatorio "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\RELATORIOS_TECNICOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5.md" `
  --outdir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_GERADOS" `
  --model "gpt-5"
```

### Saída esperada
```text
C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_GERADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5.md
```

---

### 6.3) Exportar os formatos finais do sermão

Se `exportar_formatos_sermao_md.py` estiver na raiz do projeto:

```powershell
python .\exportar_formatos_sermao_md.py `
  --md "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_GERADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5.md" `
  --outdir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS"
```

Se o script estiver em `tools\`:

```powershell
python .\tools\exportar_formatos_sermao_md.py `
  --md "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_GERADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5.md" `
  --outdir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\SERMOES_FORMATADOS"
```

### Saídas esperadas
- `...__tablet.html`
- `...__A4.html`
- `...__A5.html`
- `...__A4.docx`

---

## 7) Padrão aprovado do sermão nesta versão

A abertura do sermão deve seguir esta ordem:
1. **Título do sermão**
2. **Verso-chave**
3. **Sugestão breve de oração**
4. **Leitura do texto bíblico central**

Depois:
5. Introdução
6. Desenvolvimento
7. Aplicação
8. Conclusão

### Observação
Essa estrutura já foi validada no sermão-piloto de **Gogue e Magogue**.

---

## 8) Scripts e funções — seção de referência rápida

### Pipeline clássico de artigos

#### `baixar_anexos_pralbino_final.py`
**Função:** baixar anexos do e-mail do Pr. Albino por período e salvar em lote `YYYY-MM-DD`.

**Parâmetros:**
- `--ini` → data inicial `AAAA-MM-DD`
- `--fim` → data final `AAAA-MM-DD`
- `--data-root` → raiz de `anexos_filtrados`
- `--remetente` → padrão: `pralbino@gmail.com`
- `--so` → extensões permitidas
- `--nao-consolidar` → impede consolidação automática
- `--nao-prompts` → impede geração automática de prompts

**Exemplo:**
```powershell
python .\baixar_anexos_pralbino_final.py --ini 2026-01-01 --fim 2026-01-31 --nao-prompts
```

---

#### `normalizar_titulos_pasta.py`
**Função:** normalizar nomes dos `.docx`, ajustar título interno e opcionalmente copiar para `DOCX_NORMALIZADOS`.

**Parâmetros:**
- `--data-root`
- `--lote`
- `--copiar-normalizados`
- `--modo {publicacao,sermoes,nenhum}`

**Exemplo:**
```powershell
python .\normalizar_titulos_pasta.py --lote 2025-11-25 --copiar-normalizados --modo sermoes
```

---

#### `listar_artigos_docx_paginas.py`
**Função:** medir páginas / tamanho e ajudar a identificar artigos curtos, médios e longos.

**Parâmetros:**
- `--input-dir`
- `--saida`
- `--soffice`
- `--max`
- `--keep-pdfs`

**Exemplo:**
```powershell
python .\listar_artigos_docx_paginas.py --input-dir "..\2025-11-25" --saida ".."
```

---

#### `segmentar_docx_pralbino.py`
**Função:** segmentar artigos por subtítulos e, opcionalmente, dividir seções longas.

**Parâmetros:**
- `--input-dir`
- `--saida`
- `--area`
- `--split-long`
- `--max-words-section`
- `--split-target-words`
- `--zip`

**Exemplo:**
```powershell
python .\segmentar_docx_pralbino.py --input-dir "PASTA_DE_ENTRADA" --saida "PASTA_DE_SAIDA" --split-long --zip
```

---

#### `consolidar_serie_por_esboco.py`
**Função:** consolidar um lote em uma série, com base no ESBOÇO e fuzzy match.

**Parâmetros:**
- `--data-root`
- `--lote`
- `--series`
- `--continue-series`
- `--threshold`

**Exemplo:**
```powershell
python .\consolidar_serie_por_esboco.py --lote 2025-11-25 --series "A BÍBLIA E A HISTÓRIA DA HUMANIDADE"
```

---

#### `converter_em_pdf_por_esboco.py`
**Função:** converter os `.docx` consolidados para PDF usando o `manifest.csv`.

**Parâmetros:**
- `--serie`
- `--overwrite`
- `--limit`

**Exemplo:**
```powershell
python .\converter_em_pdf_por_esboco.py --serie "A BÍBLIA E A HISTÓRIA DA HUMANIDADE" --overwrite
```

---

#### `gerar_prompts_imagens.py`
**Função:** gerar prompts de imagens a partir do `manifest.csv` da série.

**Parâmetros:**
- `--data-root`
- `--series`
- `--npar`
- `--maxchars`

**Exemplo:**
```powershell
python .\gerar_prompts_imagens.py --series "A BÍBLIA E A HISTÓRIA DA HUMANIDADE"
```

---

#### `gerar_imagens_lote.py`
**Função:** gerar imagens em lote a partir dos prompts da série.

**Parâmetros:**
- `--dir`
- `--prompts`
- `--out`
- `--model`
- `--size`
- `--quality {low,medium,high,auto}`
- `--run`
- `--overwrite`
- `--sleep`
- `--limit`

**Exemplo de simulação:**
```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\A BÍBLIA E A HISTÓRIA DA HUMANIDADE"
```

**Exemplo de execução real:**
```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\A BÍBLIA E A HISTÓRIA DA HUMANIDADE" --run --quality low
```

---

### Pipeline novo de sermões

#### `gerar_relatorio_tecnico_de_docx.py`
**Função:** gerar relatório técnico em `.md` a partir de um artigo `.docx`.

**Parâmetros:**
- `--docx`
- `--outdir`
- `--model`
- `--max-chars`

**Exemplo:**
```powershell
python .\gerar_relatorio_tecnico_de_docx.py --docx "ARQUIVO.docx" --outdir "PASTA" --model "gpt-5" --max-chars 60000
```

---

#### `gerar_sermao_de_relatorio.py`
**Função:** gerar sermão em `.md` a partir de um relatório técnico `.md`.

**Parâmetros:**
- `--relatorio`
- `--outdir`
- `--model`

**Exemplo:**
```powershell
python .\gerar_sermao_de_relatorio.py --relatorio "ARQUIVO.md" --outdir "PASTA" --model "gpt-5"
```

---

#### `exportar_formatos_sermao_md.py`
**Função:** exportar um sermão `.md` para leitura em tablet e impressão.

**Parâmetros:**
- `--md`
- `--outdir`

**Exemplo:**
```powershell
python .\exportar_formatos_sermao_md.py --md "ARQUIVO.md" --outdir "PASTA"
```

---

## 9) Checklist final desta versão

### Para artigos / publicação
- [ ] Lote baixado ou já disponível
- [ ] Títulos normalizados
- [ ] Série consolidada
- [ ] PDFs gerados
- [ ] `manifest.csv` revisado
- [ ] Importação realizada
- [ ] Prompts gerados
- [ ] Imagens geradas, se necessário

### Para sermões
- [ ] Artigo selecionado
- [ ] Tamanho medido
- [ ] Segmentação feita, se necessário
- [ ] Relatório técnico gerado
- [ ] Relatório revisado
- [ ] Sermão gerado
- [ ] Sermão revisado
- [ ] `tablet.html` gerado
- [ ] `A4.html` gerado
- [ ] `A5.html` gerado
- [ ] `A4.docx` gerado

---

## 10) Troubleshooting rápido

### 10.1) `EMAIL_PASS = None`
- conferir `.env.local`;
- confirmar senha de app do Google.

### 10.2) LibreOffice travando em update
- concluir update/reparo;
- tentar novamente.

### 10.3) PDF faltando para 1 arquivo
- converter manualmente;
- abrir e salvar de novo no Word/LibreOffice.

### 10.4) DOCX não encontrado no fluxo de sermão
- validar com `Test-Path`;
- confirmar o caminho real com `Get-ChildItem -Recurse -Filter "*NOME*"`.

### 10.5) Erro por variável de ambiente da API
Use exatamente:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_AQUI"
```

Não usar nomes como `OpenOPENAI_API_KEY`.

### 10.6) Alguns arquivos enviados ao chat “somem” depois
Isso é limitação do ambiente do chat. Se precisar de novo, basta reenviar o arquivo específico.

---

## 11) Observação estratégica final

Nesta versão, o pipeline está fechado em dois trilhos:

1. **Artigos / publicação**
2. **Relatório técnico → sermão → formatação final**

Os dois podem compartilhar a mesma base de arquivos, mas **não precisam ser executados sempre juntos**.

O próximo upgrade deverá concentrar-se em:
- pipeline interativo seguro;
- seleção por etapa;
- checklist operacional;
- manifest enriquecido.

