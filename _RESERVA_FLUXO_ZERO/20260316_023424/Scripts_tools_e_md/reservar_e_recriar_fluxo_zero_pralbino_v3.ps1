param(
    [string]$ProjectRoot = ".",
    [switch]$DryRun,
    [switch]$Executar,
    [string]$Confirmacao = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path -LiteralPath $PathValue)) {
        if ($DryRun) {
            Write-Host "[DRY] MKDIR $PathValue"
        } else {
            New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
            Write-Host "[OK]  MKDIR $PathValue" -ForegroundColor Green
        }
    }
}

function Move-ToReserve {
    param(
        [string]$SourcePath,
        [string]$ReserveRoot,
        [string]$ProjectRootResolved
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) { return }

    $srcItem = Get-Item -LiteralPath $SourcePath -Force
    $relative = $srcItem.FullName.Substring($ProjectRootResolved.Length).TrimStart('\')
    $dest = Join-Path $ReserveRoot $relative

    if ($DryRun) {
        Write-Host "[DRY] MOVE $($srcItem.FullName) -> $dest" -ForegroundColor Yellow
    } else {
        $destParent = Split-Path -Parent $dest
        if ($destParent) { Ensure-Dir -PathValue $destParent }
        Move-Item -LiteralPath $srcItem.FullName -Destination $dest -Force
        Write-Host "[OK]  MOVE $($srcItem.FullName) -> $dest" -ForegroundColor Green
    }
}

function Copy-SelectedToWorkspace {
    param(
        [string]$FilePath,
        [string]$WorkspaceRoot
    )

    if (-not (Test-Path -LiteralPath $FilePath)) { return }
    $file = Get-Item -LiteralPath $FilePath -Force
    if ($file.PSIsContainer) { return }

    $destDir = if ($file.Name -ieq "README_ETAPA2_ORQUESTRADOR.md") {
        Join-Path $WorkspaceRoot "Docs"
    } else {
        Join-Path $WorkspaceRoot "Scripts"
    }

    $destPath = Join-Path $destDir $file.Name

    if ($DryRun) {
        Write-Host "[DRY] COPY $($file.FullName) -> $destPath" -ForegroundColor Magenta
    } else {
        Ensure-Dir -PathValue $destDir
        Copy-Item -LiteralPath $file.FullName -Destination $destPath -Force
        Write-Host "[OK]  COPY $($file.FullName) -> $destPath" -ForegroundColor Green
    }
}

function Is-RootOperationalLooseFile {
    param(
        [System.IO.FileInfo]$File,
        [string]$CurrentScriptName
    )

    $name = $File.Name
    $ext  = $File.Extension.ToLowerInvariant()

    $blockedExact = @(
        "manage.py", ".gitignore", "Procfile", "runtime.txt", "requirements.txt",
        "requirements-dev.txt", "package.json", "package-lock.json", "pyproject.toml",
        "poetry.lock", "db.sqlite3", "__init__.py", $CurrentScriptName
    )

    if ($blockedExact -contains $name) { return $false }

    $allowedExt = @(".py",".ps1",".md",".txt",".docx",".html",".htm",".json",".xlsx",".zip",".webmanifest")
    if ($allowedExt -notcontains $ext) { return $false }

    return $true
}

function Is-BadNameOrPath {
    param([string]$FullPath)

    $p = $FullPath.ToLowerInvariant().Replace("/", "\")
    $name = [System.IO.Path]::GetFileName($p)

    if ($p.Contains("\__pycache__\")) { return $true }
    if ($p.Contains("\_temp_update\")) { return $true }
    if ($p.Contains("\apenas_local\manifests\")) { return $true }
    if ($p.Contains("\apenas_local\browse\")) { return $true }
    if ($p.Contains("\a_lei_no_nt\zip\")) { return $true }

    if ($name -like "*.pyc") { return $true }
    if ($name -like "*.zip") { return $true }
    if ($name -ieq "site.webmanifest") { return $true }

    if ($name -match " \(\d+\)") { return $true }
    if ($name -match "old[_\-]") { return $true }
    if ($name -match "_old[_\-]") { return $true }

    if ($name -like "README_ETAPA2_ORQUESTRADOR (*.md") { return $true }

    return $false
}

function Is-SelectedForFluxo {
    param([string]$FullPath)

    if (Is-BadNameOrPath -FullPath $FullPath) { return $false }

    $p = $FullPath.ToLowerInvariant().Replace("/", "\")
    $name = [System.IO.Path]::GetFileName($p)

    # único doc permitido
    if ($name -ieq "README_ETAPA2_ORQUESTRADOR.md") { return $true }

    # daqui para baixo: só scripts .py / .ps1
    $ext = [System.IO.Path]::GetExtension($name).ToLowerInvariant()
    if ($ext -notin @(".py",".ps1")) { return $false }

    $excludePatterns = @(
        "\inventariar_",
        "\rastrear_",
        "\coletar_contexto_",
        "\sanear_workspace_",
        "\recriar_estrutura_apenas_local",
        "\reservar_e_recriar_fluxo_zero_pralbino",
        "\readme_recriar_estrutura_apenas_local",
        "\readme_rastrear_",
        "\readme_inventariar_",
        "\readme_coletar_contexto_",
        "\readme_saneamento_",
        "\readme_reservar_e_recriar_fluxo_zero_pralbino",
        "\zip_repo_sanitizado",
        "\check_secrets",
        "\delete_old_iam_user",
        "\create_policy_and_attach",
        "\pdfmenu",
        "\atualizar_zips_generico",
        "\atualizar_zips_pr_albino",
        "\.git-redactions",
        "\pyrightconfig.json",
        "\teste_db_",
        "\teste_estruturado",
        "\teste_minimo",
        "\run.ps1",
        "\rodar_remoto.ps1"
    )

    foreach ($pat in $excludePatterns) {
        if ($p.Contains($pat)) { return $false }
    }

    $includeWildcards = @(
        "baixar_anexos_pralbino*",
        "baixar_referenciados_s3*",
        "baixar_restantes_fallback*",
        "filtrar_refs_uploads_artigos*",
        "exportar_refs_arquivos*",
        "classificar_em_4_series*",
        "consolidar_serie_por_esboco*",
        "converter_em_pdf_por_esboco*",
        "gerar_sermao*",
        "gerar_relatorio_tecnico*",
        "listar_artigos_docx_paginas*",
        "segmentar_docx_pralbino*",
        "comparar_modelos_sermoes_pralbino*",
        "exportar_formatos_sermao_md*",
        "normalizar_titulos_pasta*",
        "normalizar_s3_listagem*",
        "run_pipeline_pralbino*",
        "run_pipeline_sermao_completo*",
        "pipeline_publicar_sermao*",
        "publicar_sermao_local*",
        "importar_artigos_publicar*",
        "importar_um_artigo*",
        "orquestrador_sermoes*",
        "sermoes_inventory*",
        "sermoes_browse*",
        "sermoes_runner*"
    )

    foreach ($wc in $includeWildcards) {
        if ($name -like $wc) { return $true }
    }

    return $false
}

function Get-SelectionScore {
    param([string]$FullPath)

    $p = $FullPath.ToLowerInvariant().Replace("/", "\")

    $score = 0

    if ($p.Contains("\tools\pralbino_pipeline\")) { $score += 500 }
    elseif ($p.Contains("\scripts\publicacao\")) { $score += 450 }
    elseif ($p.Contains("\tools\pralbino_sermoes\")) { $score += 400 }
    elseif ($p.Contains("\tools\scripts\")) { $score += 300 }
    elseif ($p.Contains("\apenas_local\anexos_filtrados\scripts\")) { $score += 200 }
    else { $score += 100 }

    $name = [System.IO.Path]::GetFileName($p)

    if ($name -ieq "README_ETAPA2_ORQUESTRADOR.md") {
        if ($p -notmatch "\\") { $score += 600 }
        if ($FullPath -match "README_ETAPA2_ORQUESTRADOR\.md$") { $score += 50 }
    }

    try {
        $item = Get-Item -LiteralPath $FullPath -Force
        if ($item.Length -gt 0) { $score += 10 }
    } catch {}

    return $score
}

$resolvedRoot = (Resolve-Path $ProjectRoot).Path
$currentScriptName = [System.IO.Path]::GetFileName($PSCommandPath)

if ($resolvedRoot -notlike "*Pr_Albino_Marks*") {
    throw "Caminho recusado por segurança. ProjectRoot fora do contexto esperado: $resolvedRoot"
}

if (-not $DryRun -and -not $Executar) {
    throw "Para executar de verdade, use -Executar. Para simular, use -DryRun."
}

if ($Executar -and $Confirmacao -ne "RESERVAR_E_RECRIAR_FLUXO_ZERO") {
    throw "Confirmação inválida. Use: -Confirmacao RESERVAR_E_RECRIAR_FLUXO_ZERO"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reserveRoot = Join-Path $resolvedRoot "_RESERVA_FLUXO_ZERO\$timestamp"
$reportRoot = Join-Path $resolvedRoot "_relatorios_saneamento\fluxo_zero_v3_$timestamp"
$workspaceRoot = Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados"

Write-Step "Contexto"
Write-Host "ProjectRoot: $resolvedRoot"
Write-Host "DryRun: $DryRun"
Write-Host "Executar: $Executar"
Write-Host "Reserva: $reserveRoot"

$dirTargets = @(
    (Join-Path $resolvedRoot "Apenas_Local"),
    (Join-Path $resolvedRoot "scripts"),
    (Join-Path $resolvedRoot "tools\Scripts"),
    (Join-Path $resolvedRoot "tools\pralbino_pipeline"),
    (Join-Path $resolvedRoot "tools\pralbino_sermoes"),
    (Join-Path $resolvedRoot "A_Lei_no_NT\Zip")
)

$rootLooseFiles = @()
Get-ChildItem -LiteralPath $resolvedRoot -Force -File | ForEach-Object {
    if (Is-RootOperationalLooseFile -File $_ -CurrentScriptName $currentScriptName) {
        $rootLooseFiles += $_.FullName
    }
}

Write-Step "Preparando relatórios"
Ensure-Dir -PathValue $reportRoot

$invPath = Join-Path $reportRoot "inventario_alvos.txt"
$selPath = Join-Path $reportRoot "selecionados_para_workspace.txt"
$notesPath = Join-Path $reportRoot "notas_fluxo_zero_v3.txt"

$inv = New-Object System.Collections.Generic.List[string]
$inv.Add("INVENTARIO DE ALVOS PARA RESERVA")
$inv.Add("Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$inv.Add("Root: $resolvedRoot")
$inv.Add("")
$inv.Add("[DIRETORIOS]")
foreach ($d in $dirTargets) {
    if (Test-Path -LiteralPath $d) {
        $inv.Add($d.Substring($resolvedRoot.Length).TrimStart('\'))
    }
}
$inv.Add("")
$inv.Add("[ARQUIVOS SOLTOS NA RAIZ]")
foreach ($f in $rootLooseFiles | Sort-Object) {
    $inv.Add($f.Substring($resolvedRoot.Length).TrimStart('\'))
}

if ($DryRun) {
    Write-Host "[DRY] REPORT $invPath"
} else {
    $inv | Set-Content -LiteralPath $invPath -Encoding UTF8
    Write-Host "[OK]  REPORT $invPath" -ForegroundColor Green
}

Write-Step "Pré-selecionando candidatos do fluxo zero"
$candidates = @()
foreach ($d in $dirTargets) {
    if (Test-Path -LiteralPath $d) {
        $candidates += Get-ChildItem -LiteralPath $d -Recurse -Force -File | ForEach-Object { $_.FullName }
    }
}
$candidates += $rootLooseFiles
$candidates = $candidates | Sort-Object -Unique

$selectedMap = @{}
foreach ($c in $candidates) {
    if (-not (Test-Path -LiteralPath $c)) { continue }
    if (-not (Is-SelectedForFluxo -FullPath $c)) { continue }

    $name = [System.IO.Path]::GetFileName($c)
    $score = Get-SelectionScore -FullPath $c

    if (-not $selectedMap.ContainsKey($name)) {
        $selectedMap[$name] = [PSCustomObject]@{
            Name = $name
            Source = $c
            Score = $score
        }
    } else {
        if ($score -gt $selectedMap[$name].Score) {
            $selectedMap[$name] = [PSCustomObject]@{
                Name = $name
                Source = $c
                Score = $score
            }
        }
    }
}

$selectedItems = $selectedMap.Values | Sort-Object Name

# 1) Move tudo para a reserva
Write-Step "Movendo alvos para a reserva"
foreach ($d in $dirTargets) {
    Move-ToReserve -SourcePath $d -ReserveRoot $reserveRoot -ProjectRootResolved $resolvedRoot
}
foreach ($f in $rootLooseFiles) {
    Move-ToReserve -SourcePath $f -ReserveRoot $reserveRoot -ProjectRootResolved $resolvedRoot
}

# 2) Recria estrutura mínima de trabalho
Write-Step "Recriando estrutura mínima de trabalho"
$dirs = @(
    (Join-Path $resolvedRoot "Apenas_Local"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\Entrada_Email"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\Docs"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\HTML"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\Imagens"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\Scripts"),
    (Join-Path $resolvedRoot "Apenas_Local\anexos_filtrados\Temporarios"),
    (Join-Path $resolvedRoot "Apenas_Local\Scripts"),
    (Join-Path $resolvedRoot "Apenas_Local\Scripts\publicacao"),
    (Join-Path $resolvedRoot "Apenas_Local\Scripts_Homologados"),
    (Join-Path $resolvedRoot "Apenas_Local\Scripts_Homologados\publicacao"),
    (Join-Path $resolvedRoot "Apenas_Local\manifests"),
    (Join-Path $resolvedRoot "Apenas_Local\browse"),
    (Join-Path $resolvedRoot "Apenas_Local\SERMOES_FORMATADOS"),
    (Join-Path $resolvedRoot "Apenas_Local\SERIES_CLASSIFICADAS"),
    (Join-Path $resolvedRoot "Apenas_Local\RELATORIOS_TECNICOS"),
    (Join-Path $resolvedRoot "Apenas_Local\LOGS")
)

foreach ($d in $dirs) { Ensure-Dir -PathValue $d }

# 3) Restaura só o que interessa para o fluxo zero
Write-Step "Selecionando arquivos do fluxo zero para o workspace"
$selectedLines = New-Object System.Collections.Generic.List[string]
foreach ($item in $selectedItems) {
    $selectedLines.Add(("{0} <= {1}" -f $item.Name, $item.Source.Substring($resolvedRoot.Length).TrimStart('\')))
    Copy-SelectedToWorkspace -FilePath $item.Source -WorkspaceRoot $workspaceRoot
}

if ($DryRun) {
    Write-Host "[DRY] REPORT $selPath"
} else {
    $lines = @("SELECIONADOS PARA Apenas_Local\anexos_filtrados", "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')", "") + $selectedLines
    $lines | Set-Content -LiteralPath $selPath -Encoding UTF8
    Write-Host "[OK]  REPORT $selPath" -ForegroundColor Green
}

$notes = @(
    "LIMPEZA GERAL + RESERVA + FLUXO ZERO (v3)",
    "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "",
    "v3 endurecida:",
    "- exclui __pycache__, .pyc, _temp_update, zips, site.webmanifest",
    "- exclui nomes com (1), (2), Old_ e variantes numeradas do README",
    "- não restaura manifests/browse antigos",
    "- restaura apenas scripts do fluxo zero e README_ETAPA2_ORQUESTRADOR.md",
    "",
    "Locais movidos para reserva:",
    "- Apenas_Local",
    "- scripts",
    "- tools/Scripts",
    "- tools/pralbino_pipeline",
    "- tools/pralbino_sermoes",
    "- A_Lei_no_NT/Zip",
    "- arquivos operacionais soltos da raiz",
    "",
    "Protegido / não tocado:",
    "- apps Django",
    "- manage.py e arquivos core da aplicação",
    "- .git, venv, media, static, banco"
)

if ($DryRun) {
    Write-Host "[DRY] REPORT $notesPath"
} else {
    $notes | Set-Content -LiteralPath $notesPath -Encoding UTF8
    Write-Host "[OK]  REPORT $notesPath" -ForegroundColor Green
}

Write-Step "Concluído"
if ($DryRun) {
    Write-Host "Dry run concluído. Nada foi movido."
} else {
    Write-Host "Reserva criada em: $reserveRoot"
    Write-Host "Workspace enxuto recriado em Apenas_Local"
    Write-Host "Relatórios em: $reportRoot"
}
