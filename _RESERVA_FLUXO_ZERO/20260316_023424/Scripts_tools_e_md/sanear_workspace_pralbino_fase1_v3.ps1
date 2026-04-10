param(
    [string]$Root = ".",
    [switch]$DryRun
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
        }
    }
}

function Move-Safe {
    param(
        [string]$SourcePath,
        [string]$DestRoot
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) { return }

    $sourceItem = Get-Item -LiteralPath $SourcePath -Force
    $destPath = Join-Path $DestRoot $sourceItem.Name

    if ($DryRun) {
        Write-Host "[DRY] MOVE $SourcePath -> $destPath" -ForegroundColor Yellow
    } else {
        Ensure-Dir -PathValue $DestRoot
        Move-Item -LiteralPath $SourcePath -Destination $destPath -Force
        Write-Host "[OK] MOVE  $SourcePath -> $destPath" -ForegroundColor Green
    }
}

$rootPath = (Resolve-Path $Root).Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$quarantineRoot = Join-Path $rootPath "_quarentena_saneamento\f1_v3_$timestamp"
$reportRoot = Join-Path $rootPath "_relatorios_saneamento\f1_v3_$timestamp"

Write-Step "Contexto"
Write-Host "Root: $rootPath"
Write-Host "DryRun: $DryRun"

# 1) Quarentena automática SEGURA
# Importante: NÃO tocar no núcleo protegido da Etapa 2:
# - scripts/publicacao/**
# - *.ps1 e *.py da raiz
# - README_ETAPA2*
# - patches da etapa
# - workspace Apenas_Local
# - código Django/apps/migrations

$safeQuarantineTargets = @(
    (Join-Path $rootPath "_pacotes_chatgpt"),
    (Join-Path $rootPath "_sanitizados_preview"),
    (Join-Path $rootPath "_diagnosticos_segredos"),
    (Join-Path $rootPath "_inventario_scripts"),
    (Join-Path $rootPath "_inventario_duplicatas"),
    (Join-Path $rootPath "A_Lei_no_NT\Zip\_temp_update")
)

Write-Step "Quarentena automática segura"
foreach ($target in $safeQuarantineTargets) {
    Move-Safe -SourcePath $target -DestRoot $quarantineRoot
}

# 2) Relatórios preservacionistas
Ensure-Dir -PathValue $reportRoot

$protectedReport = Join-Path $reportRoot "nucleo_protegido_etapa2.txt"
$zeroReport = Join-Path $reportRoot "arquivos_zero_bytes.txt"
$notesReport = Join-Path $reportRoot "notas_fase1_v3.txt"

Write-Step "Mapeando núcleo protegido da Etapa 2"

$protectedLines = New-Object System.Collections.Generic.List[string]
$protectedLines.Add("NUCLEO PROTEGIDO - ETAPA 2")
$protectedLines.Add("Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$protectedLines.Add("Root: $rootPath")
$protectedLines.Add("")

# scripts/publicacao
$pubPath = Join-Path $rootPath "scripts\publicacao"
if (Test-Path -LiteralPath $pubPath) {
    $protectedLines.Add("[scripts/publicacao]")
    Get-ChildItem -LiteralPath $pubPath -Recurse -Force -File |
        Sort-Object FullName |
        ForEach-Object { $protectedLines.Add($_.FullName.Substring($rootPath.Length).TrimStart('\')) }
    $protectedLines.Add("")
}

# raiz .ps1 e .py
$protectedLines.Add("[raiz .ps1/.py]")
Get-ChildItem -LiteralPath $rootPath -Force -File |
    Where-Object { $_.Extension -in @(".ps1", ".py") } |
    Sort-Object Name |
    ForEach-Object { $protectedLines.Add($_.FullName.Substring($rootPath.Length).TrimStart('\')) }
$protectedLines.Add("")

# READMEs ETAPA2 e patches próximos
$protectedLines.Add("[README_ETAPA2 e patches]")
Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
    Where-Object {
        $_.Name -like "README_ETAPA2*" -or
        $_.Name -like "*patch*"
    } |
    Sort-Object FullName |
    ForEach-Object { $protectedLines.Add($_.FullName.Substring($rootPath.Length).TrimStart('\')) }

if ($DryRun) {
    Write-Host "[DRY] REPORT $protectedReport"
} else {
    $protectedLines | Set-Content -LiteralPath $protectedReport -Encoding UTF8
    Write-Host "[OK]  REPORT $protectedReport" -ForegroundColor Green
}

# 3) Zero-byte audit (NÃO move automaticamente)
Write-Step "Auditando arquivos zerados"
$zeroLines = New-Object System.Collections.Generic.List[string]
$zeroLines.Add("ARQUIVOS COM 0 BYTES")
$zeroLines.Add("Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$zeroLines.Add("Root: $rootPath")
$zeroLines.Add("")
$zeroLines.Add("OBS: esta fase NAO move automaticamente arquivos zerados do núcleo protegido.")
$zeroLines.Add("")

$skipTopDirs = @(
    (Join-Path $rootPath ".git"),
    (Join-Path $rootPath "venv"),
    (Join-Path $rootPath ".venv"),
    (Join-Path $rootPath "Apenas_Local"),
    (Join-Path $rootPath "_quarentena_saneamento"),
    (Join-Path $rootPath "_relatorios_saneamento")
)

$zeroFiles = Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File | Where-Object {
    $fullName = $_.FullName
    $isSkipped = $false
    foreach ($skipDir in $skipTopDirs) {
        if ($skipDir -and $fullName.StartsWith($skipDir, [System.StringComparison]::OrdinalIgnoreCase)) {
            $isSkipped = $true
            break
        }
    }
    ($_.Length -eq 0) -and (-not $isSkipped)
}

foreach ($zf in $zeroFiles | Sort-Object FullName) {
    $rel = $zf.FullName.Substring($rootPath.Length).TrimStart('\')
    $isProtected = $false
    if ($rel -like "scripts\publicacao\*") { $isProtected = $true }
    if (($zf.DirectoryName -eq $rootPath) -and ($zf.Extension -in @(".ps1", ".py"))) { $isProtected = $true }
    if ($zf.Name -like "README_ETAPA2*") { $isProtected = $true }
    $tag = if ($isProtected) { "PROTEGIDO_REVISAR" } else { "REVISAR" }
    $zeroLines.Add("[$tag] $rel")
}

if ($DryRun) {
    Write-Host "[DRY] REPORT $zeroReport"
} else {
    $zeroLines | Set-Content -LiteralPath $zeroReport -Encoding UTF8
    Write-Host "[OK]  REPORT $zeroReport" -ForegroundColor Green
}

# 4) Notas resumidas
$notes = @(
    "FASE 1 V3 - SANEAMENTO RESPONSAVEL",
    "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "",
    "Quarentena automática segura aplicada apenas a artefatos temporários:",
    "- _pacotes_chatgpt",
    "- _sanitizados_preview",
    "- _diagnosticos_segredos",
    "- _inventario_scripts",
    "- _inventario_duplicatas",
    "- A_Lei_no_NT/Zip/_temp_update",
    "",
    "Núcleo protegido da Etapa 2 (não mover automaticamente):",
    "- scripts/publicacao/**",
    "- arquivos .ps1 e .py da raiz",
    "- README_ETAPA2*",
    "- patches associados",
    "",
    "Também não tocar nesta fase:",
    "- Apenas_Local/**",
    "- código Django/apps/migrations",
    "- duplicatas ainda sob revisão comparativa"
)

if ($DryRun) {
    Write-Host "[DRY] REPORT $notesReport"
} else {
    $notes | Set-Content -LiteralPath $notesReport -Encoding UTF8
    Write-Host "[OK]  REPORT $notesReport" -ForegroundColor Green
}

Write-Step "Concluído"
if ($DryRun) {
    Write-Host "Dry run concluído. Nenhum arquivo foi movido."
} else {
    Write-Host "Fase 1 v3 concluída."
    Write-Host "Quarentena: $quarantineRoot"
    Write-Host "Relatórios: $reportRoot"
}
