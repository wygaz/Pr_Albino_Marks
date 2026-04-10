param(
    [string]$Root = "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado",
    [string]$SaidaBase = "",
    [string]$NomePacote = "",
    [switch]$IncludeWorkspacePesado,
    [switch]$IncludeDownloadsReferenciados,
    [switch]$IncludeMedia,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) {
    Write-Host "`n=== $msg ===" -ForegroundColor Cyan
}

function Ensure-Dir([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Copy-IfExists([string]$source, [string]$dest) {
    if (Test-Path -LiteralPath $source) {
        Ensure-Dir (Split-Path -Parent $dest)
        if ($DryRun) {
            Write-Host "[DRY] FILE  $source -> $dest"
        } else {
            Copy-Item -LiteralPath $source -Destination $dest -Force
        }
        return $true
    }
    return $false
}

function Copy-DirFiltered([string]$sourceDir, [string]$destDir, [string[]]$excludeDirNames = @(), [string[]]$excludeFilePatterns = @()) {
    if (-not (Test-Path -LiteralPath $sourceDir)) { return $false }

    $srcFull = (Resolve-Path -LiteralPath $sourceDir).Path
    Ensure-Dir $destDir

    $items = Get-ChildItem -LiteralPath $sourceDir -Recurse -Force
    foreach ($item in $items) {
        $full = $item.FullName
        $rel = $full.Substring($srcFull.Length).TrimStart('\\','/')
        if ([string]::IsNullOrWhiteSpace($rel)) { continue }

        $parts = $rel -split '[\\/]'
        $skip = $false

        foreach ($part in $parts) {
            if ($excludeDirNames -contains $part) {
                $skip = $true
                break
            }
        }
        if ($skip) { continue }

        if (-not $item.PSIsContainer) {
            foreach ($pattern in $excludeFilePatterns) {
                if ($item.Name -like $pattern) {
                    $skip = $true
                    break
                }
            }
        }
        if ($skip) { continue }

        $target = Join-Path $destDir $rel
        if ($item.PSIsContainer) {
            if ($DryRun) {
                Write-Host "[DRY] DIR   $full -> $target"
            } else {
                Ensure-Dir $target
            }
        } else {
            if ($DryRun) {
                Write-Host "[DRY] FILE  $full -> $target"
            } else {
                Ensure-Dir (Split-Path -Parent $target)
                Copy-Item -LiteralPath $full -Destination $target -Force
            }
        }
    }
    return $true
}

function Copy-RootMatches([string]$root, [string[]]$patterns, [string]$destDir) {
    Ensure-Dir $destDir
    foreach ($pattern in $patterns) {
        Get-ChildItem -LiteralPath $root -Force -File -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
            $dest = Join-Path $destDir $_.Name
            if ($DryRun) {
                Write-Host "[DRY] FILE  $($_.FullName) -> $dest"
            } else {
                Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
            }
        }
    }
}

if (-not (Test-Path -LiteralPath $Root)) {
    throw "Root não encontrado: $Root"
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
if ([string]::IsNullOrWhiteSpace($SaidaBase)) {
    $SaidaBase = Join-Path $Root '_pacotes_chatgpt'
}
if ([string]::IsNullOrWhiteSpace($NomePacote)) {
    $NomePacote = "pralbino_contexto_chatgpt_$timestamp"
}

$staging = Join-Path $SaidaBase $NomePacote
$zipPath = "$staging.zip"

Write-Step "Preparando pasta de saída"
Ensure-Dir $SaidaBase
if ((Test-Path -LiteralPath $staging) -and -not $DryRun) {
    Remove-Item -LiteralPath $staging -Recurse -Force
}
if ((Test-Path -LiteralPath $zipPath) -and -not $DryRun) {
    Remove-Item -LiteralPath $zipPath -Force
}
Ensure-Dir $staging

$excludeCommonDirs = @(
    '.git', '.github', '.idea', '.vscode', '.venv', 'venv', 'env',
    '__pycache__', 'node_modules', '.mypy_cache', '.pytest_cache',
    'site-packages', 'dist', 'build', 'htmlcov', '.ruff_cache'
)
$excludeCommonFiles = @('*.pyc', '*.pyo', '*.log', '*.tmp', '*.bak', '*.sqlite3', '*.db')

Write-Step "Copiando arquivos essenciais de raiz"
Copy-RootMatches -root $Root -patterns @(
    'manage.py',
    'requirements*.txt',
    'pyproject.toml',
    'Procfile',
    'runtime.txt',
    'railway.json',
    'nixpacks.toml',
    'README*',
    '*.md',
    '*.ps1',
    '*.py',
    '.gitignore',
    '.env.example',
    '.env_desenv',
    '.env_producao'
) -destDir (Join-Path $staging 'root_essencial')

Write-Step "Copiando diretórios principais do app"
$dirCandidates = @(
    'pralbinomarks',
    'artigos',
    'apps',
    'templates',
    'scripts',
    'requirements',
    'docs'
)
foreach ($dir in $dirCandidates) {
    $src = Join-Path $Root $dir
    $dst = Join-Path $staging $dir
    if ($dir -eq 'templates' -or $dir -eq 'apps' -or $dir -eq 'artigos' -or $dir -eq 'pralbinomarks' -or $dir -eq 'scripts' -or $dir -eq 'docs' -or $dir -eq 'requirements') {
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
    }
}

Write-Step "Copiando static customizado"
$staticSrc = Join-Path $Root 'static'
$staticDst = Join-Path $staging 'static'
if (Test-Path -LiteralPath $staticSrc) {
    [void](Copy-DirFiltered -sourceDir $staticSrc -destDir $staticDst -excludeDirNames ($excludeCommonDirs + @('admin')) -excludeFilePatterns $excludeCommonFiles)
}

Write-Step "Copiando scripts espalhados do workspace"
$scriptDirs = @(
    'Apenas_Local\scripts',
    'Apenas_Local\Scripts',
    'Apenas_Local\anexos_filtrados\scripts',
    'Apenas_Local\anexos_filtrados\Scripts',
    'Apenas_Local\anexos_filtrados\sermoes\producao'
)
foreach ($rel in $scriptDirs) {
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $staging $rel
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
    }
}

Write-Step "Copiando contexto operacional leve do Apenas_Local"
$lightWorkspaceDirs = @(
    'Apenas_Local\manifests',
    'Apenas_Local\browse',
    'Apenas_Local\RELATORIOS_TECNICOS',
    'Apenas_Local\SERMOES_GERADOS',
    'Apenas_Local\SERMOES_FORMATADOS'
)
foreach ($rel in $lightWorkspaceDirs) {
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $staging $rel
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
    }
}

Write-Step "Copiando contexto de saneamento/homologação"
$homologDirs = @(
    'Apenas_Local\anexos_filtrados\ESBOCOS_FILTRADOS',
    'Apenas_Local\anexos_filtrados\IMG'
)
foreach ($rel in $homologDirs) {
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $staging $rel
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
    }
}

$singleFiles = @(
    'Apenas_Local\RESULTADO_GERACAO_SERMOES.zip',
    'Apenas_Local\anexos_filtrados\relatorio_docx_paginas_20260223_211522.csv'
)
foreach ($rel in $singleFiles) {
    $src = Join-Path $Root $rel
    $dst = Join-Path $staging $rel
    [void](Copy-IfExists -source $src -dest $dst)
}

if ($IncludeWorkspacePesado) {
    Write-Step "Incluindo workspace pesado"
    $heavyDirs = @(
        'Apenas_Local\anexos_filtrados\SERIES_CLASSIFICADAS'
    )
    foreach ($rel in $heavyDirs) {
        $src = Join-Path $Root $rel
        if (Test-Path -LiteralPath $src) {
            $dst = Join-Path $staging $rel
            [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
        }
    }
}

if ($IncludeDownloadsReferenciados) {
    Write-Step "Incluindo downloads_referenciados"
    $rel = 'Apenas_Local\downloads_referenciados'
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $staging $rel
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames $excludeCommonDirs -excludeFilePatterns $excludeCommonFiles)
    }
}

if ($IncludeMedia) {
    Write-Step "Incluindo media"
    $rel = 'media'
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $staging $rel
        [void](Copy-DirFiltered -sourceDir $src -destDir $dst -excludeDirNames ($excludeCommonDirs + @('cache')) -excludeFilePatterns $excludeCommonFiles)
    }
}

Write-Step "Gerando manifesto do pacote"
$manifestPath = Join-Path $staging '_MANIFESTO_PACOTE.txt'
$manifest = @()
$manifest += "Pacote gerado para apoio de análise do projeto Pr_Albino_Marks"
$manifest += "Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$manifest += "Root: $Root"
$manifest += ""
$manifest += "Incluído por padrão:"
$manifest += "- arquivos essenciais de raiz"
$manifest += "- pralbinomarks / apps / artigos / templates / scripts / docs / requirements (se existirem)"
$manifest += "- static customizado (exclui static/admin)"
$manifest += "- scripts espalhados em Apenas_Local"
$manifest += "- manifests, browse, relatorios técnicos, sermões gerados/formatados"
$manifest += "- ESBOCOS_FILTRADOS e IMG"
$manifest += ""
$manifest += "Opcional:"
$manifest += "- IncludeWorkspacePesado => SERIES_CLASSIFICADAS"
$manifest += "- IncludeDownloadsReferenciados => downloads_referenciados"
$manifest += "- IncludeMedia => media"
$manifest += ""
$manifest += "Exclusões automáticas:"
$manifest += "- .git, .venv, venv, __pycache__, node_modules, caches, build/dist"
$manifest += "- *.pyc, *.pyo, *.log, *.tmp, *.bak, *.sqlite3, *.db"
$manifest += "- static/admin"

if ($DryRun) {
    Write-Host "[DRY] MANIFESTO -> $manifestPath"
} else {
    $manifest | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}

if (-not $DryRun) {
    Write-Step "Compactando ZIP final"
    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $zipPath -Force
    Write-Host "`nPacote criado com sucesso:" -ForegroundColor Green
    Write-Host "Pasta: $staging"
    Write-Host "ZIP:   $zipPath"
} else {
    Write-Step "Dry run concluído"
    Write-Host "Nenhum arquivo foi copiado."
}
