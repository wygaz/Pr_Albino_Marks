# Instruções — Pipeline Pr. Albino Marks (Anexos → Normalização → PDFs → Série → Prompts)

Este guia descreve como usar os scripts em `Apenas_Local/anexos_filtrados/Scripts/` para:
1) baixar anexos do e-mail do Pr. Albino;  
2) normalizar nomes/título interno dos `.docx` (remover códigos tipo `Sm1038` e padronizar em MAIÚSCULO);  
3) gerar PDFs com o mesmo nome do `.docx`;  
4) consolidar em uma **SÉRIE** mesmo quando o Pr. Albino envia “em partes”;  
5) gerar **prompts** para criação das imagens de capa.

---

## 1) Estrutura de pastas (padrão)

Dentro do projeto:

```
Apenas_Local/
  anexos_filtrados/
    Scripts/
      baixar_anexos_pralbino_final.py
      normalizar_titulos_pasta.py
      consolidar_serie_por_esboco.py
      gerar_prompts_imagens.py
    YYYY-MM-DD/                # (lote do dia; criado automaticamente)
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

- **Scripts**: onde ficam os scripts.
- **YYYY-MM-DD**: cada remessa baixada (lote), nomeada pela **data final** do período informado.
- **SERIES**: consolidação definitiva por série (para quando ele envia em partes).

---

## 2) Pré-requisitos (uma vez só)

### 2.1) Pacotes Python
No seu ambiente virtual (venv), instale:

```powershell
pip install imapclient python-dotenv python-docx
```

### 2.2) LibreOffice (para PDF)
Instale o LibreOffice (recomendado para conversão em lote).  
O script costuma localizar automaticamente; se não localizar, defina o caminho em `SOFFICE_PATH` (ver abaixo).

---

## 3) Configuração do `.env.local`

Crie/edite **na raiz do projeto** um arquivo `.env.local` com:

```env
EMAIL_USER=seuemail@gmail.com
EMAIL_PASS=SUA_SENHA_DE_APP_DE_16_CARACTERES

# Opcional (se o script não achar o LibreOffice)
SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

> **Importante:** use **Senha de app** do Google (App Password), não a senha comum.

---

## 4) Execução principal (um comando)

Entre na pasta de scripts e rode:

```powershell
cd "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts"
python .\baixar_anexos_pralbino_final.py
```

### 4.1) O que ele vai perguntar
1) **Data inicial** (opcional) — deixe em branco para “sem limite”.  
2) **Data final** (opcional) — deixe em branco para “hoje”.  

Ao final, ele pode perguntar (dependendo da versão do script):
- **Gerar PDFs agora (LibreOffice)?** → recomendado: **S**
- **Consolidar este lote em uma SÉRIE agora?** → recomendado: **S**
- **Gerar prompts de imagens?** → recomendado: **S** (se você for gerar capas em seguida)

### 4.2) Saídas esperadas
- Lote criado em: `.../anexos_filtrados/YYYY-MM-DD/`
- Dentro do lote:
  - `.docx` já renomeados para o **título do artigo** (sem data/códigos)
  - título interno (metadado `Title`) atualizado e em **MAIÚSCULO**
  - `ESBOCO.txt` (quando presente)
  - `.pdf` (se você escolheu gerar PDFs)

---

## 5) Quando o Pr. Albino enviar “em partes”

Você fará o mesmo download em outro dia (novo lote `YYYY-MM-DD`).  
Na consolidação, escolha **continuar a série anterior**.

### Rodar consolidação manualmente (se quiser)
```powershell
python .\consolidar_serie_por_esboco.py
```

Ele irá:
- sugerir a pasta `YYYY-MM-DD` mais recente;
- perguntar se você quer **continuar a série anterior**;
- criar/atualizar a pasta da série em `SERIES/`.

---

## 6) Normalização manual (se quiser “passar a régua” no lote)

Para normalizar novamente um lote (por garantia), rode:

```powershell
python .\normalizar_titulos_pasta.py
```

- Ele sugere por padrão o `YYYY-MM-DD` mais recente.
- Remove `Sm####` e padroniza em MAIÚSCULO.
- Renomeia `.docx` (e `.pdf` correspondente, se existir).

---

## 7) Gerar PDFs manualmente (após a normalização)

Se você quiser gerar PDFs depois (em lote), use o script de PDF do seu pipeline (ou rode o passo interno do principal).  
Como regra: **gerar PDF só depois do `.docx` estar com o nome final**.

> Se precisar, dá para converter diretamente via LibreOffice:
```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir . ".\ARQUIVO.docx"
```

---

## 8) Prompts de imagens (capas)

Gere prompts para a série:

```powershell
python .\gerar_prompts_imagens.py
```

Ele cria em `SERIES/NOME_DA_SERIE/`:
- `prompts_imagens.txt` (pronto para copiar/colar)
- `prompts_imagens.csv` (organizado por ordem)

### Como os prompts são montados
- Título da série + título do artigo  
- Resumo curto baseado nos **5 primeiros parágrafos** do `.docx`  
- Instrução para **não** colocar texto na imagem (sem letras, números, marcas d’água)

---

## 9) Esboço e ordem de publicação

- O arquivo `ESBOCO.txt` define a ordem cronológica preparada pelo Pr. Albino.
- A consolidação cria um `manifest.csv` com:
  - ordem
  - título do esboço
  - status (OK / DUVIDOSO / FALTANDO)

**Regra prática:**
- `OK` → publicar
- `DUVIDOSO` → ajustar à mão (renomear/checar)
- `FALTANDO` → ainda não foi recebido

---

## 10) Troubleshooting (problemas comuns)

### 10.1) Erro de senha (EMAIL_PASS = None)
- Confirme `.env.local` com `EMAIL_PASS` preenchido.
- Confirme que você está usando **senha de app**.

### 10.2) LibreOffice “Update / Please wait…”
- Isso trava conversões em lote.
- Conclua o update/reparo (Configurações → Apps → LibreOffice → Reparar) e tente de novo.

### 10.3) PDF “faltando” para 1 arquivo específico
- Converta só aquele arquivo manualmente.
- Se persistir, abra o DOCX e “Salvar como…” (corrige corrupção leve) e reconverta.

### 10.4) Títulos variam levemente
- O consolidado usa normalização + fuzzy match.
- Se cair como `DUVIDOSO`, ajuste manualmente o nome do `.docx` para casar com o ESBOÇO.

---

## 11) Checklist final antes de publicar

- [ ] Todos os `.docx` do lote com nome “limpo” e em MAIÚSCULO  
- [ ] PDFs gerados com o mesmo nome  
- [ ] `manifest.csv` sem itens `FALTANDO` (ou consciente do que falta)  
- [ ] `prompts_imagens.txt` gerado (se for criar capas)  
- [ ] Consolidado em `SERIES/NOME_DA_SERIE/` se a série estiver sendo enviada em partes

Sequência oficial:
1. baixar_anexos_pralbino_final.py
2. consolidar_serie_por_esboco.py (com dedupe da linha de título da série)
3. converter_em_pdf_por_esboco.py
4. python manage.py importar_serie --serie "..."
5. gerar_prompts_imagens.py
6. gerar_imagens_lote.py (depois de resolver Billing/limits)


## Argparse (Python) — referência rápida

### O que é
`argparse` é um módulo padrão do Python para receber parâmetros pela linha de comando.

### Como ver as opções de um script
```powershell
python seu_script.py -h

======================= Como rodar a conversao para PDF de forma avulsa: ============================

Da pasta Scripts:

cd "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts"
python .\converter_em_pdf_por_esboco.py

Ou forçando a série:
python .\converter_em_pdf_por_esboco.py --serie "A BÍBLIA E A HISTÓRIA DA HUMANIDADE"

====================================== gerar imagens ==========================================

Como rodar (modo web barato)
python .\gerar_imagens_lote.py --dir "..\SERIES\A BÍBLIA E A HISTÓRIA DA HUMANIDADE"

Se quiser paisagem, mas ainda barato
python .\gerar_imagens_lote.py --dir "..\SERIES\A BÍBLIA E A HISTÓRIA DA HUMANIDADE" --size 1536x1024 --quality low

============================== PARA PUBLICAR depois de pronta a série ======================================
Local:
    $env:ENV_NAME="local"
    python manage.py importar_serie --serie "A BÍBLIA E A HISTÓRIA DA HUMANIDADE" (com a opção de rodar sobrescrevendo) --overwrite-media
Remoto:
    $env:ENV_NAME="remoto"
    python manage.py importar_serie --serie "A BÍBLIA E A HISTÓRIA DA HUMANIDADE" --dry-run --limit 3
    python manage.py importar_serie --serie "A BÍBLIA E A HISTÓRIA DA HUMANIDADE"

===============================  atualizar_zips_generico.ps1  =================================
# Pr_Albino_Marks_restaurado\atualizar_zips_generico.ps1
#Requires -Version 5.1
'''
=================================    Como usar (fluxo rápido)    =================================
        A) Criar o arquivo de jobs (uma vez)
        .\atualizar_zips_generico.ps1 -InitConfig 


        Isso cria zip_jobs.json ao lado do .ps1. Edite os zips/sources conforme seu projeto.

        B) Rodar normal (cria ZIPs novos com timestamp)
        .\atualizar_zips_generico.ps1 -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado"

        C) Rodar “only-newer”
        .\atualizar_zips_generico.ps1 -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" -OnlyNewer

        D) “inplace + only-newer”
        .\atualizar_zips_generico.ps1 -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" -OnlyNewer -InPlace

        E) Se quiser garantir por conteúdo (hash)
        .\atualizar_zips_generico.ps1 -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" -OnlyNewer -Hash sha256
=================================================================================================
'''