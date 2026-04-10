# Instruções Organizadas — Pipeline Pr. Albino Marks

Este documento reorganiza as instruções operacionais do projeto **Pr. Albino Marks**, eliminando repetições e separando os fluxos por objetivo.  
O material original misturava orientações de **anexos**, **normalização**, **PDF**, **consolidação de séries**, **prompts de imagens**, **publicação** e algumas notas rápidas de uso. Aqui tudo fica em uma sequência mais clara.

---

## 1) Objetivo deste conjunto de scripts

Os scripts localizados em `Apenas_Local/anexos_filtrados/Scripts/` servem para apoiar quatro frentes principais:

1. **Captura de material**  
   Baixar anexos enviados por e-mail pelo Pr. Albino.

2. **Preparação dos artigos**  
   Normalizar nomes dos arquivos `.docx`, atualizar o título interno e gerar PDFs com o nome final correto.

3. **Consolidação por série**  
   Unir artigos recebidos em partes dentro de uma pasta única de série, com esboço e manifesto de controle.

4. **Materiais auxiliares**  
   Gerar prompts para imagens de capa e preparar o caminho para publicação/importação.

---

## 2) Estrutura de pastas esperada

Dentro do projeto:

```text
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
    YYYY-MM-DD/                # lote do dia
    DOCX_NORMALIZADOS/         # opcional, apoio para fluxo de sermões
    SERIES/
      NOME_DA_SERIE/
        ESBOCO_YYYY-MM-DD.txt
        manifest.csv
        prompts_imagens.txt
        prompts_imagens.csv
        DOCX/
        PDF/
        IMG/
```

### Significado das pastas

- **Scripts/**: scripts utilitários do pipeline.
- **YYYY-MM-DD/**: lote bruto ou semibruto de um dia de recebimento.
- **DOCX_NORMALIZADOS/**: cópia de apoio para seleção, medição e preparação de sermões.
- **SERIES/**: consolidação oficial por série, com arquivos já organizados para publicação.

---

## 3) Pré-requisitos

### 3.1) Pacotes Python
No `venv` do projeto:

```powershell
pip install imapclient python-dotenv python-docx
```

### 3.2) LibreOffice
O LibreOffice é o caminho preferencial para conversão em lote para PDF.

Se o script não localizar automaticamente, usar no `.env.local`:

```env
SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

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
- `SOFFICE_PATH` é opcional, mas útil quando a conversão para PDF não encontra o LibreOffice sozinha.

---

## 5) Fluxos operacionais

# 5A) Fluxo completo — quando ainda é preciso baixar anexos do e-mail

Use este fluxo quando os arquivos ainda **não** estão no lote local.

### Passo 1 — Baixar anexos

```powershell
cd "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts"
python .\baixar_anexos_pralbino_final.py
```

O script pode perguntar:
- data inicial;
- data final;
- se deve gerar PDFs;
- se deve consolidar a série;
- se deve gerar prompts de imagens.

### Saídas esperadas
- criação de um lote em `anexos_filtrados/YYYY-MM-DD/`;
- `.docx` renomeados;
- título interno atualizado;
- PDFs gerados, se escolhido;
- possível consolidação em série.

---

# 5B) Fluxo reduzido — quando os artigos já estão extraídos localmente

Este é o fluxo mais importante para o momento atual.

Use quando os `.docx` já estão em algo como:

```text
Apenas_Local/anexos_filtrados/2025-11-25/
```

### Passo 1 — Normalizar títulos do lote

```powershell
python .\normalizar_titulos_pasta.py --lote 2025-11-25
```

### Passo 2 — Consolidar a série

```powershell
python .\consolidar_serie_por_esboco.py
```

ou, quando quiser forçar a série:

```powershell
python .\consolidar_serie_por_esboco.py --lote 2025-11-25 --series "NOME DA SÉRIE"
```

### Passo 3 — Converter a série em PDF

```powershell
python .\converter_em_pdf_por_esboco.py
```

ou:

```powershell
python .\converter_em_pdf_por_esboco.py --serie "NOME DA SÉRIE"
```

### Passo 4 — Importar no projeto Django

```powershell
python manage.py importar_serie --serie "NOME DA SÉRIE"
```

### Passo 5 — Gerar prompts de imagens

```powershell
python .\gerar_prompts_imagens.py
```

### Passo 6 — Gerar imagens em lote

```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\NOME DA SÉRIE"
```

ou em paisagem, qualidade baixa:

```powershell
python .\gerar_imagens_lote.py --dir "..\SERIES\NOME DA SÉRIE" --size 1536x1024 --quality low
```

---

# 5C) Fluxo de sermões — a partir dos artigos já extraídos

Este fluxo é complementar ao de artigos.

## Objetivo
Usar os artigos já recebidos para preparar sermões em DOCX e PDF, com controle por série, artigo e eventual segmento.

## Etapa sugerida

### 1. Normalizar o lote

```powershell
python .\normalizar_titulos_pasta.py --lote 2025-11-25 --copiar-normalizados --modo sermoes
```

> Quando usado com `--copiar-normalizados`, o script copia DOCX e PDFs correspondentes para `DOCX_NORMALIZADOS/<lote>/`, sem mover os originais.

### 2. Medir tamanho dos artigos

```powershell
python .\listar_artigos_docx_paginas.py --input-dir "..\2025-11-25" --saida ".."
```

### 3. Segmentar artigos longos, se necessário

```powershell
python .\segmentar_docx_pralbino.py --input-dir "PASTA_DE_ENTRADA" --saida "PASTA_DE_SAIDA" --split-long --zip
```

Esse script:
- segmenta por subtítulos;
- pode dividir seções muito longas;
- ajuda a reduzir custo e esforço de manuseio em textos extensos.

### 4. Preparar o sermão

O sermão pode ser gerado:
- a partir do artigo inteiro;
- ou a partir de um segmento numerado.

### 5. Revisar DOCX final

Antes do PDF:
- conferir título;
- conferir estrutura do sermão;
- conferir se a formatação está “pronta para auditoria”.

### 6. Converter o sermão final em PDF

Sempre depois da versão DOCX final estar estável.

---

## 6) Scripts principais e suas funções

### `baixar_anexos_pralbino_final.py`
Baixa anexos do e-mail e organiza em lote `YYYY-MM-DD`.

### `normalizar_titulos_pasta.py`
- renomeia `.docx` com base no título do artigo;
- atualiza o título interno do DOCX;
- renomeia o PDF correspondente, se existir;
- pode copiar o resultado para `DOCX_NORMALIZADOS`;
- pode sugerir o próximo passo (`publicacao`, `sermoes` ou `nenhum`).

### `listar_artigos_docx_paginas.py`
Conta páginas e ajuda a identificar artigos curtos, médios e longos.

### `segmentar_docx_pralbino.py`
Divide artigos por subtítulos e, opcionalmente, por tamanho.

### `consolidar_serie_por_esboco.py`
Monta ou continua a pasta oficial da série em `SERIES/NOME_DA_SERIE/`.

### `converter_em_pdf_por_esboco.py`
Converte para PDF com base na série consolidada e no `manifest.csv`.

### `gerar_prompts_imagens.py`
Cria prompts para capas em texto e CSV.

### `gerar_imagens_lote.py`
Executa a geração das imagens com base nos prompts.

---

## 7) Ordem oficial de publicação

Quando o objetivo é publicação dos artigos, a sequência oficial fica assim:

1. `baixar_anexos_pralbino_final.py`  
2. `consolidar_serie_por_esboco.py`  
3. `converter_em_pdf_por_esboco.py`  
4. `python manage.py importar_serie --serie "..."`  
5. `gerar_prompts_imagens.py`  
6. `gerar_imagens_lote.py`  

> Se os anexos já estiverem extraídos, o passo 1 pode ser pulado.

---

## 8) Controle por esboço e manifesto

O arquivo `ESBOCO.txt` define a ordem da série.  
O `manifest.csv` funciona como painel de controle.

### Status esperados
- `OK` → item pronto ou reconhecido corretamente;
- `DUVIDOSO` → exige conferência manual;
- `FALTANDO` → ainda não recebido.

### Regra prática
- Publicar os itens `OK`;
- revisar os `DUVIDOSO`;
- aguardar ou localizar os `FALTANDO`.

---

## 9) Conversão avulsa para PDF

Quando precisar converter manualmente um único arquivo:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir . ".\ARQUIVO.docx"
```

---

## 10) Troubleshooting

### 10.1) `EMAIL_PASS = None`
- conferir `.env.local`;
- confirmar senha de app do Google.

### 10.2) LibreOffice travando em update
- concluir update/reparo;
- tentar novamente a conversão.

### 10.3) Um DOCX específico não gera PDF
- converter manualmente;
- se necessário, abrir no Word/LibreOffice e salvar de novo.

### 10.4) Título levemente diferente do esboço
- deixar o consolidado usar o fuzzy match;
- se ficar `DUVIDOSO`, renomear manualmente para casar melhor com o esboço.

### 10.5) Ambiente de sermões com textos longos
- medir antes com `listar_artigos_docx_paginas.py`;
- segmentar quando o tamanho dificultar o processamento.

---

## 11) Checklist final

### Para artigos / publicação
- [ ] DOCX com nome limpo e consistente  
- [ ] Título interno do DOCX ajustado  
- [ ] PDF com o mesmo nome do DOCX  
- [ ] Série consolidada em `SERIES/NOME_DA_SERIE/`  
- [ ] `manifest.csv` revisado  
- [ ] Importação realizada  
- [ ] Prompts de imagens gerados, se necessário  

### Para sermões
- [ ] Artigo base identificado  
- [ ] Tamanho medido  
- [ ] Segmentação feita, se necessário  
- [ ] Sermão DOCX preparado  
- [ ] Sermão DOCX revisado  
- [ ] Sermão PDF convertido  

---

## 12) Referência rápida — `argparse`

### O que é
`argparse` é o módulo padrão do Python para receber parâmetros pela linha de comando.

### Como ver opções de um script

```powershell
python seu_script.py -h
```

Use isso sempre que quiser confirmar:
- parâmetros aceitos;
- valores opcionais;
- nomes corretos dos argumentos.

---

## 13) Observação estratégica

Este manual organiza o pipeline em dois trilhos:

1. **Artigos / publicação**  
   foco em consolidar série, converter PDF, importar e gerar capas.

2. **Sermões / auditoria / derivação**  
   foco em reaproveitar os artigos já recebidos para produzir sermões formatados, com eventual segmentação.

Os dois trilhos compartilham a mesma base de arquivos, mas não precisam ser executados sempre juntos.
