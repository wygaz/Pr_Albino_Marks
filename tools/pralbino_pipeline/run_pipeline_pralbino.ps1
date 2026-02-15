param(
  [string]$Ini = "",
  [string]$Fim = "",
  [string]$Remetente = "pralbino@gmail.com",

  # Onde fica a pasta anexos_filtrados (fora do git). Ex.: C:\...\Apenas_Local\anexos_filtrados
  [string]$DataRoot = "",

  # Se vocÃª quiser rodar em um lote jÃ¡ existente (YYYY-MM-DD):
  [string]$Lote = "",

  # Comportamento do preparo
  [switch]$SkipDbCheck,
  [switch]$AllowRemote,
  [ValidateSet("", "local", "remoto")] [string]$EnvName = "",

  [switch]$SkipDownload,
  [switch]$SkipNormalize,
  [switch]$SkipConsolidate,
  [switch]$ContinueSeries,
  [double]$Threshold = 0.84,
  [switch]$SkipPDF,
  [switch]$OverwritePDF,
  [int]$PdfLimit = 0,
  [switch]$SkipPrompts,
  [int]$NPar = 5,
  [int]$MaxChars = 420,

  # Imagens (opcional / custo) â€“ default: NÃƒO gera
  [switch]$GenerateImages,
  [ValidateSet("1024x1024","1536x1024","1024x1536")] [string]$ImageSize = "1024x1024",
  [ValidateSet("low","medium","high","auto")] [string]$ImageQuality = "low",
  [int]$ImageLimit = 0,
  [switch]$OverwriteImages,

  # PublicaÃ§Ã£o no Django (import_series) â€“ default: SIM (se manage.py existir)
  [switch]$SkipImport,
  [switch]$ImportDryRun,

  [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-RepoRoot([string]$StartDir) {
  $cur = Resolve-Path $StartDir
  while ($true) {
    if (Test-Path (Join-Path $cur "manage.py")) { return $cur }
    if (Test-Path (Join-Path $cur ".git")) { return $cur }
    $parent = Split-Path $cur -Parent
    if ($parent -eq $cur) { return $null }
    $cur = $parent
  }
}

function Resolve-DataRoot([string]$RepoRoot, [string]$DataRootArg) {
  if ($DataRootArg -and $DataRootArg.Trim()) {
    return (Resolve-Path $DataRootArg).Path
  }

  $cand = Join-Path $RepoRoot "Apenas_Local\anexos_filtrados"
  if (Test-Path $cand) {
    return (Resolve-Path $cand).Path
  }

  throw "DataRoot nÃ£o informado e nÃ£o encontrei '$cand'. Passe -DataRoot."
}

function Get-LatestLoteDir([string]$BaseDir) {
  $re = '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
  $dirs = Get-ChildItem -Path $BaseDir -Directory -ErrorAction SilentlyContinue |
          Where-Object { $_.Name -match $re } |
          Sort-Object Name
  if (@($dirs).Count -eq 0) { return $null }
  return $dirs[-1].FullName
}

function Read-LastSeries([string]$ScriptsDir) {
  $p = Join-Path $ScriptsDir ".last_series.txt"
  if (Test-Path $p) {
    $v = (Get-Content $p -Raw).Trim()
    if ($v) { return $v }
  }
  return $null
}

function Resolve-SeriesName([string]$BaseDir, [string]$ScriptsDir) {
  $last = Read-LastSeries $ScriptsDir

  $seriesRoot = Join-Path $BaseDir "SERIES"
  if (-not (Test-Path $seriesRoot)) { return $last }

  $dirs = Get-ChildItem -Path $seriesRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name
  if (@($dirs).Count -eq 0) { return $last }

  # Preferir o que estiver em .last_series.txt; se nÃ£o existir, pega o mais recente por nome
  if ($last) {
    $cand = Join-Path $seriesRoot $last
    if (Test-Path $cand) { return $last }
  }

  return $dirs[-1].Name
}

function Invoke-Step([string]$Title, [string[]]$PyArgs, [string]$WorkDir = "") {
  Write-Host "\n=== $Title ===" -ForegroundColor Cyan
  if ($WorkDir) {
    Push-Location $WorkDir
    try {
      & $PythonExe @PyArgs
    } finally {
      Pop-Location
    }
  } else {
    & $PythonExe @PyArgs
  }
}

function Assert-DbSafe([string]$RepoRoot) {
  if ($SkipDbCheck) { return }

  if ($EnvName -and $EnvName.Trim()) {
    $env:ENV_NAME = $EnvName
  }

  $dbCheck = Join-Path $RepoRoot "tools\db_check.py"
  if (-not (Test-Path $dbCheck)) {
    Write-Host "(db_check.py nÃ£o encontrado em tools/. Pulando checagem automÃ¡tica.)" -ForegroundColor Yellow
    return
  }

  Write-Host "\n=== DB CHECK (trava anti-desastre) ===" -ForegroundColor Cyan
  $out = & $PythonExe $dbCheck 2>&1
  $out | ForEach-Object { Write-Host $_ }

  $hostLine = ($out | Select-String -Pattern '^HOST\s*=\s*(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (-not $hostLine) { return }

  $dbHost = $hostLine.Matches[0].Groups[1].Value.Trim()
  $isLocal = ($dbHost -match 'localhost') -or ($dbHost -match '127\.0\.0\.1')

  if (-not $isLocal -and -not $AllowRemote) {
    throw "ABORTADO: HOST do BD nÃ£o parece local ('$dbHost'). Para prosseguir no remoto, use -AllowRemote e -EnvName remoto."
  }
}

# -----------------------------
# START
# -----------------------------
$ScriptsDir = $PSScriptRoot
$RepoRoot = Find-RepoRoot $ScriptsDir
if (-not $RepoRoot) {
  throw "NÃ£o encontrei manage.py/.git subindo a partir de: $ScriptsDir"
}

$BaseDir = Resolve-DataRoot $RepoRoot $DataRoot

Assert-DbSafe $RepoRoot

# paths dos scripts python
$pyDownload   = Join-Path $ScriptsDir "baixar_anexos_pralbino_final.py"
$pyNormalize  = Join-Path $ScriptsDir "normalizar_titulos_pasta.py"
$pyConsolidar = Join-Path $ScriptsDir "consolidar_serie_por_esboco.py"
$pyPdf        = Join-Path $ScriptsDir "converter_em_pdf_por_esboco.py"
$pyPrompts    = Join-Path $ScriptsDir "gerar_prompts_imagens.py"
$pyImages     = Join-Path $ScriptsDir "gerar_imagens_lote.py"

# 1) Download
if (-not $SkipDownload) {
  $args = @(
    $pyDownload,
    "--data-root", $BaseDir,
    "--remetente", $Remetente
  )
  if ($Ini) { $args += @("--ini", $Ini) }
  if ($Fim) { $args += @("--fim", $Fim) }

  # MantÃ©m o download "puro" no orquestrador; consolidaÃ§Ã£o/prompt ficam nos passos abaixo
  $args += @("--nao-consolidar", "--nao-prompts")

  Invoke-Step "1) Baixar anexos" $args $RepoRoot
}

# define lote
if (-not $Lote) {
  $latest = Get-LatestLoteDir $BaseDir
  if (-not $latest) { throw "Nenhum lote YYYY-MM-DD encontrado em: $BaseDir" }
  $Lote = Split-Path $latest -Leaf
}

# 2) Normalize
if (-not $SkipNormalize) {
  Invoke-Step "2) Normalizar tÃ­tulos (DOCX)" @(
    $pyNormalize,
    "--data-root", $BaseDir,
    "--lote", $Lote
  ) $RepoRoot
}

# 3) Consolidar
if (-not $SkipConsolidate) {
  $args = @(
    $pyConsolidar,
    "--data-root", $BaseDir,
    "--lote", $Lote,
    "--threshold", ("{0}" -f $Threshold)
  )
  if ($ContinueSeries) { $args += "--continue-series" }

  Invoke-Step "3) Consolidar lote em SÃ‰RIE" $args $RepoRoot
}

# SÃ©rie
$Serie = Resolve-SeriesName $BaseDir $ScriptsDir
if (-not $Serie) { throw "NÃ£o consegui resolver o nome da sÃ©rie (rode consolidaÃ§Ã£o ou crie .last_series.txt)." }
$SeriesDir = Join-Path (Join-Path $BaseDir "SERIES") $Serie

# 4) PDF
if (-not $SkipPDF) {
  $args = @(
    $pyPdf,
    "--data-root", $BaseDir,
    "--serie", $Serie
  )
  if ($OverwritePDF) { $args += "--overwrite" }
  if ($PdfLimit -gt 0) { $args += @("--limit", "$PdfLimit") }

  Invoke-Step "4) Converter DOCXâ†’PDF" $args $RepoRoot
}

# 5) Prompts
if (-not $SkipPrompts) {
  Invoke-Step "5) Gerar prompts de imagens" @(
    $pyPrompts,
    "--data-root", $BaseDir,
    "--series", $Serie,
    "--npar", "$NPar",
    "--maxchars", "$MaxChars"
  ) $RepoRoot
}

# 5.5) Imagens (opcional)
if ($GenerateImages) {
  $args = @(
    $pyImages,
    "--dir", $SeriesDir,
    "--size", $ImageSize,
    "--quality", $ImageQuality,
    "--run"
  )
  if ($OverwriteImages) { $args += "--overwrite" }
  if ($ImageLimit -gt 0) { $args += @("--limit", "$ImageLimit") }

  Invoke-Step "5.5) GERAR imagens (API)" $args $RepoRoot
} else {
  Write-Host "\n(Imagens) Pulado. Para gerar (com consumo), use -GenerateImages." -ForegroundColor DarkYellow
}

# 6) Import / publicaÃ§Ã£o
if (-not $SkipImport) {
  $manage = Join-Path $RepoRoot "manage.py"
  if (-not (Test-Path $manage)) {
    Write-Host "manage.py nÃ£o encontrado. Pulando import." -ForegroundColor Yellow
  } else {
    # tenta import_series; se falhar, cai para importar_serie
    $cmd = "import_series"
    $test = & $PythonExe $manage $cmd "--help" 2>$null
    if ($LASTEXITCODE -ne 0) { $cmd = "importar_serie" }

    $args = @(
      $manage,
      $cmd,
      "--serie", $Serie,
      "--base", (Join-Path $BaseDir "SERIES")
    )
    if ($ImportDryRun) { $args += "--dry-run" }

    Invoke-Step "6) Importar sÃ©rie no Django ($cmd)" $args $RepoRoot
  }
} else {
  Write-Host "\n(Import) Pulado. Para publicar, remova -SkipImport." -ForegroundColor DarkYellow
}

Write-Host "\nâœ… Pipeline concluÃ­do." -ForegroundColor Green
Write-Host "DataRoot : $BaseDir"
Write-Host "Lote     : $Lote"
Write-Host "SÃ©rie    : $Serie"



