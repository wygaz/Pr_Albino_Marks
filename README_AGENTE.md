# README_AGENTE

## Objetivo
Este arquivo registra as instrucoes operacionais mais importantes do pipeline do projeto **Pr. Albino Marks**, com foco em:

- nova serie vinda por e-mail;
- artigos complementares de series ja existentes;
- promocao para a base operacional;
- atualizacao do manifesto;
- abertura do Browse.

Os comandos abaixo devem ser usados em **linha unica** no terminal.

---

## Regra central do esboco

O arquivo canonico do esboco geral e:

```text
Apenas_Local\anexos_filtrados\Docs\ESBOCO_Geral.docx
```

Compatibilidade:

- o pipeline ainda aceita o nome antigo `ESBOCO_Geral_Series_1_a_4.docx`;
- o nome novo deve ser o padrao daqui para frente.

---

## Comportamento esperado para novas ocorrencias

### 1. Se vier uma nova serie por e-mail
O pipeline **nao adivinha** sozinho que um conjunto de artigos pertence a uma nova serie.

Para a nova serie ser reconhecida corretamente, e necessario:

1. atualizar o `ESBOCO_Geral.docx`;
2. incluir a nova serie no esboco;
3. se a serie **nao tiver artigo de apresentacao**, isso deve ficar claro no proprio esboco, como no caso de `TEMAS DIVERSOS`.

### 2. Se vier artigo complementar de serie ja existente
O pipeline tambem nao adivinha sozinho se esse artigo:

- substitui um artigo ja existente;
- complementa a serie como novo item;
- ou pertence a outra serie.

Nesse caso, a classificacao correta depende de o `ESBOCO_Geral.docx` estar atualizado com:

- a serie correta;
- a ordem correta;
- o titulo correto.

### 3. Regra do primeiro artigo da serie
A regra padrao do pipeline e:

- o primeiro item da serie costuma repetir o titulo da propria serie;
- esse item funciona como artigo de apresentacao.

Excecao validada:

- `TEMAS DIVERSOS` pode existir como serie **sem** artigo de apresentacao.

---

## Fluxo operacional resumido

### Etapa 1. Baixar artigos
Baixa artigos dos e-mails.

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\baixar_anexos_pralbino_esbocos.py" --ini 2026-04-25 --modo artigos
```

### Etapa 2. Baixar esbocos
Usar quando for preciso validar se chegou um novo esboco por e-mail.

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\baixar_anexos_pralbino_esbocos.py" --ini 2026-04-25 --modo esbocos
```

### Etapa 3. Preparar o lote
Classifica o lote com base no `ESBOCO_Geral.docx`.

Exemplo:

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\preparacao_do_ambiente_operacional.py" organizar-lote --artigos-dir ".\Apenas_Local\anexos_filtrados\2026_05_11-02" --esboco ".\Apenas_Local\anexos_filtrados\Docs\ESBOCO_Geral.docx" --saida ".\Apenas_Local\anexos_filtrados\2026_05_11-02\ambiente_operacional"
```

Saidas importantes:

- `preparacao_lote.csv`
- `preparacao_lote.json`
- `faltantes.csv`
- `ja_promovidos_operacional.csv`
- `alertas_titulo.csv`

Interpretacao:

- `faltantes`: faltam de verdade no lote e no operacional;
- `ja_promovidos_operacional`: nao vieram no lote, mas ja existem no operacional;
- `alertas_titulo`: divergencias que precisam ser tratadas antes de prosseguir.

### Etapa 4. Promover para o operacional

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\promover_lote_para_operacional.py" --lote 2026_05_11-02 --clear-existing
```

Resultado esperado:

- series promovidas;
- arquivos copiados;
- relatorio CSV;
- relatorio JSON.

### Etapa 5. Atualizar manifesto e abrir o Browse
Este e o comando que atualiza o manifesto, sobe o helper e abre o Browse.

```powershell
.\scripts\artigos_sermoes\abrir_browse_operacional.ps1
```

Se o script acima falhar, usar contingencia:

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\orquestrador_sermoes.py" --input-dir ".\Apenas_Local\operacional\sermoes\formatados" --input-dir-artigos ".\Apenas_Local\operacional\artigos\series" --workspace-artigos ".\Apenas_Local\operacional\artigos\series" --browse --scan-only
```

---

## Tutorial do pipeline

### 1. Baixar esbocos
`BAIXA OS ESBOCOS DOS E-MAILS A PARTIR DA DATA INFORMADA`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\baixar_anexos_pralbino_esbocos.py" --ini 2026-04-26 --modo esbocos
```

### 2. Baixar artigos
`BAIXA OS ARTIGOS DOS E-MAILS A PARTIR DA DATA INFORMADA`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\baixar_anexos_pralbino_esbocos.py" --ini 2026-04-26 --modo artigos
```

### 3. Organizar o lote
`ORGANIZA O LOTE USANDO O ESBOCO GERAL ATUALIZADO`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\preparacao_do_ambiente_operacional.py" organizar-lote --artigos-dir ".\Apenas_Local\anexos_filtrados\2026_05_11-02" --esboco ".\Apenas_Local\anexos_filtrados\Docs\ESBOCO_Geral.docx" --saida ".\Apenas_Local\anexos_filtrados\2026_05_11-02\ambiente_operacional"
```

### 4. Promover para o operacional
`PROMOVE O LOTE PREPARADO PARA A BASE OPERACIONAL`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\promover_lote_para_operacional.py" --lote 2026_05_11-02 --clear-existing
```

### 5. Carregar a chave da OpenAI
`CARREGA A OPENAI_API_KEY DO .ENV.LOCAL PARA A SESSAO ATUAL DO TERMINAL`

```powershell
Get-Content ".\.env.local" | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' } | ForEach-Object { $parts = $_ -split '=',2; if ($parts.Length -eq 2) { $env:OPENAI_API_KEY = $parts[1].Trim().Trim('"').Trim("'") } }
```

### 6. Abrir o Browse no remoto
`ABRE O BROWSE OPERACIONAL E REGENERA O MANIFESTO NO ALVO REMOTO`

```powershell
.\scripts\artigos_sermoes\abrir_browse_operacional.ps1 -PublishTarget remoto
```

### 7. Abrir o Browse no local
`ABRE O BROWSE OPERACIONAL E REGENERA O MANIFESTO NO ALVO LOCAL`

```powershell
.\scripts\artigos_sermoes\abrir_browse_operacional.ps1 -PublishTarget local
```

### 8. Gerar prompts de imagem
`GERA OS PROMPTS DE IMAGEM DOS ARTIGOS OPERACIONAIS`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\gerar_prompts_imagens_operacional.py" --series-root ".\Apenas_Local\operacional\artigos\series" --out-root ".\Apenas_Local\operacional\artigos\prompts_imagem"
```

### 9. Gerar ou refazer imagens
`GERA OU REFAZ AS IMAGENS DOS ARTIGOS A PARTIR DO CSV DE PROMPTS`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\gerar_imagens_lote_operacional.py" --prompts-csv ".\Apenas_Local\operacional\artigos\prompts_imagem\prompts_imagens_operacional.csv" --out-root ".\Apenas_Local\operacional\artigos\imagens" --run --overwrite
```

### 10. Gerar ou refazer PDFs
`GERA OU REFAZ OS PDFS DOS ARTIGOS OPERACIONAIS`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\gerar_pdfs_artigos_operacional.py" --series-root ".\Apenas_Local\operacional\artigos\series" --out-root ".\Apenas_Local\operacional\artigos\pdfs"
```

### 11. Publicar no remoto
No Browse, no contexto `Artigos sem sermao`, selecione os itens e rode o `step 6`.

### 12. Testar BD remoto e AWS com um artigo
`TESTA AS CREDENCIAIS DO BD REMOTO E DO AWS PUBLICANDO UM ARTIGO ESPECIFICO NO AMBIENTE REMOTO`

```powershell
$env:ENV_NAME="remoto"; & ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\publicar_artigos_operacional.py" --docx-path ".\Apenas_Local\operacional\artigos\series\Serie_3__a-lei-torah-nomos-mandamentos-ordenancas-e-a-graca\16__salvacao-pela-fe-na-graca.docx" --series-root ".\Apenas_Local\operacional\artigos\series" --pdf-root ".\Apenas_Local\operacional\artigos\pdfs" --img-root ".\Apenas_Local\operacional\artigos\imagens" --django-settings pralbinomarks.settings --publish-kinds all
```

### 13. Regenerar o Browse por contingencia
`REGENERA O BROWSE POR CONTINGENCIA, SEM O SCRIPT PS1`

```powershell
& ".\venv\Scripts\python.exe" ".\scripts\artigos_sermoes\orquestrador_sermoes.py" --input-dir ".\Apenas_Local\operacional\sermoes\formatados" --input-dir-artigos ".\Apenas_Local\operacional\artigos\series" --workspace-artigos ".\Apenas_Local\operacional\artigos\series" --browse --scan-only
```

### 14. Listar logs recentes
`LISTA OS LOGS MAIS RECENTES DA PUBLICACAO`

```powershell
Get-ChildItem ".\Apenas_Local\scripts\homologacao" -Filter "publicacao_sermoes_lote_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime | Format-Table -AutoSize
```

### 15. Abrir o log mais recente
`ABRE O LOG MAIS RECENTE DA PUBLICACAO NO TERMINAL`

```powershell
$log=(Get-ChildItem ".\Apenas_Local\scripts\homologacao" -Filter "publicacao_sermoes_lote_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; Get-Content $log -TotalCount 300
```

---

## Como descobrir a mensagem real de erro

As falhas importantes do pipeline nem sempre aparecem completas na tela do Browse. O lugar mais confiavel para ver a causa real e o log mais recente de publicacao.

### 1. Listar os logs mais recentes
`LISTA OS LOGS MAIS RECENTES DA PUBLICACAO`

```powershell
Get-ChildItem ".\Apenas_Local\scripts\homologacao" -Filter "publicacao_sermoes_lote_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime | Format-Table -AutoSize
```

### 2. Abrir o log mais recente
`ABRE O LOG MAIS RECENTE DA PUBLICACAO NO TERMINAL`

```powershell
$log=(Get-ChildItem ".\Apenas_Local\scripts\homologacao" -Filter "publicacao_sermoes_lote_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; Get-Content $log -TotalCount 300
```

### 3. Procurar so as linhas de erro no log mais recente
`EXTRAI SOMENTE AS LINHAS DE ERRO DO LOG MAIS RECENTE`

```powershell
$log=(Get-ChildItem ".\Apenas_Local\scripts\homologacao" -Filter "publicacao_sermoes_lote_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; Select-String -Path $log -Pattern "STATUS=ERROR|\[ERRO\]|Traceback|InvalidAccessKeyId|Forbidden|RuntimeError"
```

### 4. Regra pratica
- se o Browse continuar mostrando pendencia depois de um step, olhar primeiro o log
- se o log tiver `STATUS=ERROR`, a operacao nao concluiu
- se o log nao tiver erro, mas o manifesto nao refletir a mudanca, regenerar o Browse

---

## Falhas comuns

`O step 6 foi executado, mas o artigo continua pendente`
- abrir o log mais recente
- se houver `STATUS=ERROR`, a publicacao nao concluiu
- no remoto, os erros mais provaveis sao AWS/S3 ou `DATABASE_URL`

`O Browse mostra docx/img/pdf locais, mas BD DOCX/PDF/IMG continuam NAO`
- isso significa que os arquivos existem localmente
- mas ainda nao foram publicados no alvo atual
- se o alvo for `remoto`, falta publicacao remota

`O artigo sumiu do contexto artigos sem sermao`
- pode ter sido publicado no alvo atual
- ou o manifesto pode ter sido regenerado com outro ambiente
- conferir a faixa `Banco de Dados Local/Remoto`

`O step 5 rodou, mas o PDF nao aparece no Browse`
- verificar se o PDF foi realmente criado em `Apenas_Local\operacional\artigos\pdfs`
- depois regenerar o Browse

`O step 6 remoto falha com InvalidAccessKeyId`
- conferir `AWS_ACCESS_KEY_ID`
- conferir `AWS_SECRET_ACCESS_KEY`
- conferir se o `.env.remoto` esta alinhado com o Railway

`O step 6 remoto falha com HeadObject Forbidden`
- normalmente indica problema no storage remoto
- conferir credenciais, bucket, regiao e permissoes

`O terminal ficou estranho e executa linha por linha`
- usar sempre comandos em linha unica
- evitar blocos com crase

---

## Condicionais mais usadas

### Caso A. Veio uma nova serie

1. Atualizar `ESBOCO_Geral.docx`.
2. Rodar `organizar-lote`.
3. Conferir se a nova serie apareceu em `ambiente_operacional`.
4. Rodar `promover_lote_para_operacional.py`.
5. Abrir o Browse.

### Caso B. Veio artigo complementar de serie existente

1. Atualizar `ESBOCO_Geral.docx` com a ordem nova.
2. Rodar `organizar-lote`.
3. Validar em `preparacao_lote.csv` se o artigo foi para a serie e ordem certas.
4. Rodar `promover_lote_para_operacional.py`.
5. Abrir o Browse.

### Caso C. Veio esboco novo por e-mail

1. Baixar em `--modo esbocos`.
2. Comparar com `ESBOCO_Geral.docx`.
3. Se estiver correto, substituir o esboco canonico.
4. Rodar o preparo do lote.

### Caso D. O lote acusa muitos faltantes

1. Verificar `ja_promovidos_operacional.csv`.
2. Se os itens estiverem la, nao sao faltantes reais.
3. So tratar como faltante o que continuar em `faltantes.csv`.

### Caso E. Serie sem artigo de apresentacao

1. Registrar isso claramente no `ESBOCO_Geral.docx`.
2. Nao criar artigo ficticio so para satisfazer a regra.
3. O caso validado hoje e `TEMAS DIVERSOS`.

---

## Observacao de encoding

Evitar copiar para scripts qualquer texto mojibake vindo do terminal.

Padrao de seguranca:

- editar codigo em ASCII/UTF-8 seguro;
- nao reutilizar texto contaminado da saida do terminal como fonte de patch;
- manter o `ESBOCO_Geral.docx` como fonte canonica humana.
