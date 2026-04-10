# Etapa 2 — Orquestrador de Sermões (Rodada 4)

Esta rodada aprofunda duas correções estruturais que apareceram no browse real:

1. **Série e Autor agora podem ser hidratados pelo BD Django**
2. **Artefatos ficaram mais compactos no browse**

## O que mudou

### 1) Hidratação do manifest pelo BD
O orquestrador agora tenta ler `Artigo` do projeto Django e preencher metadados do manifest usando a regra acordada:

**override manual → manifest anterior → BD → heurística da pasta**

Na prática:
- `Série = área` do `Artigo.area.nome`
- `Autor = autor` do `Artigo.autor.nome`
- quando possível, também hidrata o título oficial do artigo
- o match é tentado primeiro por `slug`, depois por `título`

Se o BD não estiver acessível, o scan continua normalmente e apenas exibe aviso.

### 2) Browse mais legível nos artefatos
A coluna de artefatos foi compactada:
- verde: nome do artefato em minúsculas
- vermelho: nome do artefato em MAIÚSCULAS

Assim fica legível mesmo em impressão sem cor.

### 3) Títulos de coluna com ordenação visível
Os cabeçalhos continuam clicáveis e agora mostram a direção da ordenação.

### 4) Metadados de BD visíveis
Cada linha agora mostra, quando houver match:
- `Artigo #id`
- tipo de match (`slug` ou `titulo`)
- `artigo_slug`
- `artigo_titulo`

## Arquivos atualizados
- `scripts/publicacao/sermoes_inventory.py`
- `scripts/publicacao/sermoes_browse.py`
- `scripts/publicacao/orquestrador_sermoes.py`
- `scripts/publicacao/sermoes_django.py` **(novo)**

## Como aplicar
Extraia este patch **na raiz do projeto** e permita substituição dos arquivos existentes.

## Comando de teste
Se estiver na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publicacao\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\SERMOES_FORMATADOS" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```

Se estiver **dentro de** `scripts\publicacao`:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_orquestrador_sermoes.ps1 `
  -Root "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado" `
  -InputDir "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\SERMOES_FORMATADOS" `
  -ScanOnly `
  -Browse `
  -OpenBrowse
```

## Desligando a hidratação do BD
Se quiser testar só o scan de arquivos:

```powershell
--no-db-hydrate
```

## Forçando um settings module específico
Se necessário:

```powershell
--django-settings pralbinomarks.settings
```

## Próxima continuidade natural
Com esta rodada, o browse de sermões formatados fica mais maduro. A próxima frente natural é abrir o **contexto de artigos sem sermão**, reutilizando a mesma interface para geração em lote.
