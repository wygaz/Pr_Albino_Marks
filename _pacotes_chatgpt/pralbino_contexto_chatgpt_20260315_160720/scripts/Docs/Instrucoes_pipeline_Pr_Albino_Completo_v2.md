# Instruções Unificadas — Pipeline Pr. Albino Marks

Este arquivo consolida a versão atual do pipeline do projeto **Pr. Albino Marks** em um único manual operacional.

Ele cobre três trilhos principais:

1. **extração e publicação de artigos**;
2. **geração de sermões a partir de `.docx`**;
3. **publicação de sermões no app Django `sermoes`**.

Também inclui:
- comandos prontos com parâmetros;
- função de cada script;
- checklist da versão atual;
- troubleshooting prático do que já foi validado.

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
10. Converter os HTMLs do sermão para:
   - `tablet.pdf`
   - `A4.pdf`
   - `A5.pdf`
11. Publicar ou atualizar o sermão no app Django `sermoes`, com:
   - conteúdo HTML;
   - DOCX A4;
   - PDF Tablet;
   - PDF A4;
   - PDF A5.

### O que ficou para upgrade futuro
- pipeline interativo com modo seguro `[s/N]`;
- checklist com marcação automática por etapa;
- manifest enriquecido para controlar relatório técnico, sermão, formatação e publicação;
- publicação em lote de sermões;
- trava por membros / grupos no acesso aos sermões.

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
        run_pipeline_pralbino.ps1
      YYYY-MM-DD/
      DOCX_NORMALIZADOS/
      SERIES/
      SERIES_CLASSIFICADAS/
    RELATORIOS_TECNICOS/
    SERMOES_GERADOS/
    SERMOES_FORMATADOS/
  scripts/
    publicacao/
      gerar_sermao_de_docx.py
      publicar_sermao_local.py
      pipeline_publicar_sermao.py
      html_para_pdf_playwright.py
  gerar_relatorio_tecnico_de_docx.py
  gerar_sermao_de_relatorio.py
  exportar_formatos_sermao_md.py
```

### Significado das pastas principais
- `Apenas_Local/anexos_filtrados/Scripts/`: pipeline clássico de artigos.
- `YYYY-MM-DD/`: lote bruto ou semibruto de anexos baixados por data.
- `DOCX_NORMALIZADOS/`: apoio para seleção e preparação de sermões.
- `SERIES/`: consolidação oficial por série para publicação de artigos.
- `SERIES_CLASSIFICADAS/`: apoio para seleção de artigos por série no fluxo de sermões.
- `RELATORIOS_TECNICOS/`: saída dos relatórios técnicos em `.md`.
- `SERMOES_GERADOS/`: saída dos sermões em `.md`.
- `SERMOES_FORMATADOS/`: saídas finais de leitura, impressão e publicação.
- `scripts/publicacao/`: scripts do projeto ligados à publicação e ao encadeamento final dos sermões.

---

## 3) Pré-requisitos

### 3.1) Pacotes Python
No `venv` do projeto:

```powershell
pip install imapclient python-dotenv python-docx playwright
```

### 3.2) Navegador do Playwright
Usado na conversão `HTML -> PDF` dos sermões.

```powershell
playwright install
```

### 3.3) LibreOffice
Usado para conversão em lote de artigos `.docx -> .pdf`.

Se o caminho não for encontrado automaticamente, configurar no `.env.local`:

```env
SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

### 3.4) Chave da API (relatório técnico, sermão e imagens)
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
- credenciais sensíveis devem ficar no `.env.local` ou `.env.remoto`, nunca hardcoded nos scripts.

---

## 5) Os três pipelines oficiais desta versão

# 5A) Pipeline 1 — extração e publicação de artigos

## Objetivo
Sair do e-mail ou do lote local e chegar até:
- série consolidada;
- PDFs gerados;
- importação no Django;
- prompts de imagem e imagens, se necessário.

## Script-orquestrador
```text
Apenas_Local\anexos_filtrados\Scripts\run_pipeline_pralbino.ps1
```

## Entrar na pasta dos scripts
```powershell
cd "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts"
```

### Exemplo 1 — fluxo completo, puxando do e-mail
```powershell
powershell -ExecutionPolicy Bypass -File .\run_pipeline_pralbino.ps1 `
  -Ini "2026-01-01" `
  -Fim "2026-01-31"
```

### Exemplo 2 — fluxo local, sem baixar de novo
```powershell
powershell -ExecutionPolicy Bypass -File .\run_pipeline_pralbino.ps1 `
  -Lote "2025-11-25" `
  -SkipDownload
```

### Exemplo 3 — fluxo local, pulando etapas já concluídas
```powershell
powershell -ExecutionPolicy Bypass -File .\run_pipeline_pralbino.ps1 `
  -Lote "2025-11-25" `
  -SkipDownload `
  -SkipNormalize `
  -SkipConsolidate
```

### Saídas esperadas
- lote em `anexos_filtrados/YYYY-MM-DD/`;
- normalização dos `.docx`;
- série consolidada em `SERIES/<NOME_DA_SERIE>/`;
- `manifest.csv`;
- pasta `PDF/` da série;
- importação no Django;
- prompts e imagens, se executados.

---

# 5B) Pipeline 2 — geração de sermões a partir de `.docx`

## Objetivo
Sair de um artigo `.docx` e gerar:
1. relatório técnico `.md`;
2. sermão `.md`;
3. `tablet.html`;
4. `A4.html`;
5. `A5.html`;
6. `A4.docx`.

## Opção A — wrapper único
Script esperado em:
```text
scripts\publicacao\gerar_sermao_de_docx.py
```

### Modelo de comando do wrapper
```powershell
python .\scripts\publicacao\gerar_sermao_de_docx.py `
  --docx ".\Apenas_Local\anexos_filtrados\SERIES_CLASSIFICADAS\Serie_02 - APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO\A BESTA, SUA MARCA, SEU NOME E SEU NÚMERO.docx" `
  --out-relatorios ".\Apenas_Local\RELATORIOS_TECNICOS" `
  --out-sermoes ".\Apenas_Local\SERMOES_GERADOS" `
  --out-formatados ".\Apenas_Local\SERMOES_FORMATADOS" `
  --model "gpt-5"
```

> Este comando representa o **modelo desejado de orquestração** do pipeline de geração quando ele estiver consolidado em um único wrapper.

## Opção B — fluxo validado em 3 comandos
Quando ainda estiver usando os scripts separados:

### Passo 1 — gerar relatório técnico
```powershell
python .\gerar_relatorio_tecnico_de_docx.py `
  --docx ".\Apenas_Local\anexos_filtrados\SERIES_CLASSIFICADAS\Serie_02 - APOCALIPSE 17 E O PRINCÍPIO DO SIMBOLISMO\A BESTA, SUA MARCA, SEU NOME E SEU NÚMERO.docx" `
  --outdir ".\Apenas_Local\RELATORIOS_TECNICOS" `
  --model "gpt-5" `
  --max-chars 60000
```

### Passo 2 — gerar sermão
```powershell
python .\gerar_sermao_de_relatorio.py `
  --relatorio ".\Apenas_Local\RELATORIOS_TECNICOS\A BESTA, SUA MARCA, SEU NOME E SEU NÚMERO__relatorio_tecnico__gpt-5.md" `
  --outdir ".\Apenas_Local\SERMOES_GERADOS" `
  --model "gpt-5"
```

### Passo 3 — exportar formatos finais
```powershell
python .\exportar_formatos_sermao_md.py `
  --md ".\Apenas_Local\SERMOES_GERADOS\A BESTA, SUA MARCA, SEU NOME E SEU NÚMERO__relatorio_tecnico__gpt-5__sermao__gpt-5.md" `
  --outdir ".\Apenas_Local\SERMOES_FORMATADOS"
```

### Saídas esperadas
- `...__relatorio_tecnico__gpt-5.md`
- `...__relatorio_tecnico__gpt-5__sermao__gpt-5.md`
- `...__tablet.html`
- `...__A4.html`
- `...__A5.html`
- `...__A4.docx`

---

# 5C) Pipeline 3 — publicação de sermões no app Django

## Objetivo
Sair dos arquivos formatados do sermão e chegar até:
- `A4.pdf`
- `A5.pdf`
- `tablet.pdf`
- registro criado ou atualizado no app `sermoes`
- página pública com downloads funcionando.

## Script de publicação simples
```text
scripts\publicacao\publicar_sermao_local.py
```

### Quando usar
Use este script quando os PDFs já existirem ou quando você quiser apenas testar a automação da publicação no Django.

### Exemplo mínimo
```powershell
python .\scripts\publicacao\publicar_sermao_local.py `
  --titulo "Gogue e Magogue" `
  --serie "Apocalipse 17 e o Princípio do Simbolismo" `
  --resumo "Sermão-piloto publicado via script local." `
  --slug "gogue-e-magogue" `
  --ordem 1 `
  --visivel `
  --html-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.html" `
  --docx-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.docx"
```

### Exemplo completo, com PDFs já gerados
```powershell
python .\scripts\publicacao\publicar_sermao_local.py `
  --titulo "Gogue e Magogue" `
  --serie "Apocalipse 17 e o Princípio do Simbolismo" `
  --resumo "Sermão-piloto publicado via script local." `
  --slug "gogue-e-magogue" `
  --ordem 1 `
  --visivel `
  --html-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.html" `
  --pdf-tablet ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__tablet.pdf" `
  --pdf-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.pdf" `
  --pdf-a5 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A5.pdf" `
  --docx-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.docx"
```

## Script de pipeline unificado
```text
scripts\publicacao\pipeline_publicar_sermao.py
```

### Quando usar
Use este script quando você quiser:
1. converter os HTMLs em PDF;
2. extrair o HTML do sermão para o site;
3. atualizar o registro no Django;
4. anexar DOCX e PDFs num único comando.

### Comando validado do pipeline unificado
```powershell
python .\scripts\publicacao\pipeline_publicar_sermao.py `
  --titulo "Gogue e Magogue" `
  --serie "Apocalipse 17 e o Princípio do Simbolismo" `
  --resumo "Sermão publicado pelo pipeline local." `
  --ordem 1 `
  --visivel `
  --html-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.html" `
  --html-a5 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A5.html" `
  --html-tablet ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__tablet.html" `
  --docx-a4 ".\Apenas_Local\SERMOES_FORMATADOS\GOGUE E MAGOGUE__relatorio_tecnico__gpt-5__sermao__gpt-5__A4.docx"
```

### Saídas esperadas
- `...__A4.pdf`
- `...__A5.pdf`
- `...__tablet.pdf`
- atualização do registro em `sermoes`
- URL pública com downloads válidos.

---

## 6) Padrão aprovado do sermão nesta versão

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

Essa estrutura já foi validada no sermão-piloto de **Gogue e Magogue**.

---

## 7) Scripts e funções — referência rápida

### Pipeline clássico de artigos
- `run_pipeline_pralbino.ps1`  
  **Função:** orquestrar extração, normalização, consolidação, PDFs, importação e apoio às imagens.

- `baixar_anexos_pralbino_final.py`  
  **Função:** baixar anexos do e-mail do Pr. Albino por período.

- `normalizar_titulos_pasta.py`  
  **Função:** normalizar nomes dos `.docx`, ajustar título interno e opcionalmente copiar para `DOCX_NORMALIZADOS`.

- `listar_artigos_docx_paginas.py`  
  **Função:** medir páginas / tamanho para apoio de classificação e seleção.

- `segmentar_docx_pralbino.py`  
  **Função:** segmentar artigos por subtítulos e, se necessário, dividir seções longas.

- `consolidar_serie_por_esboco.py`  
  **Função:** consolidar um lote em uma série com base no ESBOÇO e fuzzy match.

- `converter_em_pdf_por_esboco.py`  
  **Função:** converter os `.docx` consolidados para PDF usando o `manifest.csv`.

- `gerar_prompts_imagens.py`  
  **Função:** gerar prompts de imagens a partir do `manifest.csv`.

- `gerar_imagens_lote.py`  
  **Função:** gerar imagens em lote a partir dos prompts da série.

### Pipeline de geração de sermões
- `gerar_sermao_de_docx.py`  
  **Função esperada:** orquestrar relatório técnico, sermão e formatação a partir de um `.docx`.

- `gerar_relatorio_tecnico_de_docx.py`  
  **Função:** gerar relatório técnico em `.md` a partir de um artigo `.docx`.

- `gerar_sermao_de_relatorio.py`  
  **Função:** gerar sermão em `.md` a partir de um relatório técnico `.md`.

- `exportar_formatos_sermao_md.py`  
  **Função:** exportar o sermão `.md` para HTMLs e DOCX final.

### Pipeline de publicação de sermões
- `html_para_pdf_playwright.py`  
  **Função:** converter HTML em PDF usando Playwright.

- `publicar_sermao_local.py`  
  **Função:** criar ou atualizar o registro do sermão no Django a partir dos arquivos prontos.

- `pipeline_publicar_sermao.py`  
  **Função:** encadear conversão `HTML -> PDF` e publicação no app `sermoes`.

---

## 8) Checklist final desta versão

### Para artigos / publicação
- [ ] Lote baixado ou já disponível
- [ ] Títulos normalizados
- [ ] Série consolidada
- [ ] PDFs dos artigos gerados
- [ ] `manifest.csv` revisado
- [ ] Importação realizada
- [ ] Prompts gerados
- [ ] Imagens geradas, se necessário

### Para sermões — geração
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

### Para sermões — publicação
- [ ] `A4.pdf` gerado
- [ ] `A5.pdf` gerado
- [ ] `tablet.pdf` gerado
- [ ] Registro atualizado no app `sermoes`
- [ ] URL pública testada
- [ ] Downloads testados
- [ ] DOCX A4 testado

---

## 9) Troubleshooting rápido

### 9.1) `EMAIL_PASS = None`
- conferir `.env.local`;
- confirmar senha de app do Google.

### 9.2) LibreOffice travando em update
- concluir update/reparo;
- tentar novamente.

### 9.3) PDF faltando para 1 arquivo no pipeline clássico
- converter manualmente;
- abrir e salvar de novo no Word/LibreOffice.

### 9.4) DOCX não encontrado no fluxo de sermão
- validar com `Test-Path`;
- confirmar o caminho real com `Get-ChildItem -Recurse -Filter "*NOME*"`.

### 9.5) Erro por variável de ambiente da API
Use exatamente:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_AQUI"
```

Não usar nomes como `OpenOPENAI_API_KEY`.

### 9.6) `ModuleNotFoundError: No module named 'pralbinomarks'`
Se o script estiver em `scripts\publicacao\`, usar no topo:

```python
BASE_DIR = Path(__file__).resolve().parents[2]
```

e não `parents[1]`.

### 9.7) PowerShell preso em `>>`
Normalmente é sintaxe incompleta:
- aspas não fechadas;
- última linha ainda com crase;
- comando multiline sem término correto.

### 9.8) `run_pipeline_sermao_completo.ps1` falhando em algum passo
- confira se o `venv` está ativo;
- confira `OPENAI_API_KEY` na sessão atual;
- valide se `pipeline_publicar_sermao.py` está em `scripts\publicacao\`;
- valide se os diretórios `RELATORIOS_TECNICOS`, `SERMOES_GERADOS` e `SERMOES_FORMATADOS` existem ou podem ser criados.

### 9.9) `/sermoes/` abrindo 404
No `urls.py` principal, a rota:

```python
path('sermoes/', include('sermoes.urls')),
```

deve vir **antes** do include raiz de `A_Lei_no_NT`, para evitar captura indevida por rota genérica com `slug`.

### 9.10) Alguns arquivos enviados ao chat “somem” depois
Isso é limitação do ambiente do chat. Se precisar de novo, basta reenviar o arquivo específico.

---

## 10) Observação estratégica final

Nesta versão, o projeto está organizado em **três trilhos**:

1. **Artigos / extração / publicação**
2. **Geração de sermões**
3. **Publicação de sermões**
4. **Pipeline completo de ponta a ponta**

Eles podem compartilhar a mesma base de arquivos, mas **não precisam ser executados sempre juntos**.

O próximo upgrade deverá concentrar-se em:
- publicação em lote de sermões;
- checklist operacional com marcação automática;
- manifest enriquecido;
- controle de acesso por membros.
