# Operações de publicação — Pr. Albino Marks

Pacote de scripts para:

1. publicar todo o acervo local de uma vez;
2. gerar backup remoto (JSON + opcionalmente full PostgreSQL + S3);
3. limpar a publicação remota e o S3;
4. espelhar a publicação local para o remoto e para o S3.

## Arquivos

- `run_publicar_todo_acervo_local.ps1`
- `backup_remoto_bd_e_s3.ps1`
- `limpar_remoto_bd_e_s3.ps1`
- `espelhar_local_para_remoto_bd_e_s3.ps1`
- `dump_publicacao_site.py`
- `reset_publicacao_site.py`
- `publicar_sermoes_lote.py`
- `db_url_info.py`

## 1) Publicar todo o acervo no local

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\run_publicar_todo_acervo_local.ps1 -ExecuteReset
```

Observações:
- publica artigos a partir de `Apenas_Local\operacional\artigos\series`, `pdfs` e `imagens`;
- publica sermões a partir de `Apenas_Local\operacional\sermoes\formatados`;
- usa `pipeline_publicar_sermao.py` da trilha ativa/versionada, com fallback para `scripts\homologacao\pipeline`.

## 2) Backup remoto

### seguro (conteúdo do site + S3)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\backup_remoto_bd_e_s3.ps1
```

### incluindo backup full do PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\backup_remoto_bd_e_s3.ps1 -FullDatabase
```

## 3) Limpar remoto

### dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\limpar_remoto_bd_e_s3.ps1
```

### executar de fato

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\limpar_remoto_bd_e_s3.ps1 -Execute
```

## 4) Espelhar local -> remoto

### modo seguro (conteúdo do site via fixture JSON + S3)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\espelhar_local_para_remoto_bd_e_s3.ps1
```

### modo full PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\artigos_sermoes\ops\espelhar_local_para_remoto_bd_e_s3.ps1 -FullDatabase
```

## Observações importantes

- Os scripts assumem perfis `.env.local` e `.env.remoto` já existentes.
- O modo seguro espelha **a publicação do site** (`Area`, `Autor`, `Artigo`, `Sermao`) e o `media/` local para o bucket remoto.
- O modo full depende de `pg_dump` e `pg_restore` no `PATH`.
- Antes de espelhar, é recomendável executar o backup remoto.
- Em operações destrutivas, rode primeiro sem `-Execute` quando houver essa opção.
