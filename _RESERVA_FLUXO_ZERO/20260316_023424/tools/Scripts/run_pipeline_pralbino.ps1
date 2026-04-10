# Pr_Albino_Marks_restaurado\Apenas_Local\anexos_filtrados\Scripts\run_pipeline_pralbino.ps1

param(
  [string]$Ini = "",
  [string]$Fim = "",
  [string]$Remetente = "pralbino@gmail.com",

  # Se você quiser rodar em um lote já existente:
  [string]$Lote = "",

  # Comportamento
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

  # Python
  [string]$PythonExe = "python"
)

if ($Ini -like "--*") { throw "Você usou --Ini. Em PowerShell use -Ini (um hífen)." }
if ($Fim -like "--*") { throw "Você usou --Fim. Em PowerShell use -Fim (um hífen)." }
if ($Remetente -like "--*") { throw "Parâmetros deslocados. Provável uso de -- em vez de -." }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# força terminal em UTF-8 (VSCode/Windows costuma precisar)
chcp 65001 | Out-Null
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$ScriptsDir = $PSScriptRoot
$BaseDir    = (Resolve-Path (Join-Path $ScriptsDir "..")).Path  # ...\anexos_filtrados

function Invoke-Step([string]$Title, [string[]]$ArgList) {

  if (-not $ArgList -or $ArgList.Count -eq 0) {
    throw "ArgList vazio em '$Title' (isso abriria o REPL do Python)."
  }

  Write-Host "`n=== $Title ===" -ForegroundColor Cyan
  Write-Host ("$PythonExe " + ($ArgList -join " ")) -ForegroundColor DarkGray

  & $PythonExe @ArgList

  if ($LASTEXITCODE -ne 0) {
    throw "Falhou: $Title (exit code $LASTEXITCODE)"
  }
}

function Get-LatestLoteDir([string]$Base) {
  $dirs = @(
    Get-ChildItem -Path $Base -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } |
      Sort-Object Name -Descending
  )

  if ($dirs.Length -eq 0) { return $null }
  return $dirs[0].Name
}

function Read-LastSeries([string]$Scripts) {
  $p = Join-Path $Scripts ".last_series.txt"
  if (!(Test-Path $p)) { return "" }

  $s = Get-Content -Path $p -Raw -Encoding UTF8
  $s = $s.Trim()
  $s = $s.Trim([char]0xFEFF)  # remove BOM se existir
  return $s
}

function Resolve-SeriesName([string]$SeriesRaw) {
  if (-not $SeriesRaw) { return "" }

  $seriesRoot = Join-Path $BaseDir "SERIES"
  if (!(Test-Path $seriesRoot)) { return $SeriesRaw }

  # se existir exato, ok
  $exact = Join-Path $seriesRoot $SeriesRaw
  if (Test-Path $exact) { return $SeriesRaw }

  # normaliza (remove acentos, lower, espaços)
  function Norm([string]$s) {
    if ($null -eq $s) { $s = "" }

    $t = $s.ToLowerInvariant()
    $t = $t.Normalize([Text.NormalizationForm]::FormD)

    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $t.ToCharArray()) {
      if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
        [void]$sb.Append($ch)
      }
    }

    $t = $sb.ToString()
    $t = ($t -replace '\s+', ' ').Trim()
    return $t
  }

  $want = Norm $SeriesRaw
  $dirs = Get-ChildItem -Path $seriesRoot -Directory -ErrorAction SilentlyContinue

  foreach ($d in $dirs) {
    if ((Norm $d.Name) -eq $want) { return $d.Name }
  }
  foreach ($d in $dirs) {
    if ((Norm $d.Name) -like "*$want*") { return $d.Name }
  }

  return $SeriesRaw
}

Push-Location $ScriptsDir
try {
  # 1) Download (opcional)
  if (-not $SkipDownload) {
    $pyArgs = @(
        ".\baixar_anexos_pralbino_final.py",
        "--remetente", $Remetente,
        "--nao-consolidar",
        "--nao-prompts"
    )
    if ($Ini) { $pyArgs += @("--ini", $Ini) }
    if ($Fim) { $pyArgs += @("--fim", $Fim) }

    Invoke-Step "1) Baixar anexos" $pyArgs
  }


  # Decide LOTE
  if (-not $Lote) {
    $Lote = Get-LatestLoteDir $BaseDir
    if (-not $Lote) { throw "Não achei nenhuma pasta de lote YYYY-MM-DD em $BaseDir." }
  }
  Write-Host "`n>> LOTE selecionado: $Lote" -ForegroundColor Yellow

  # 2) Normalizar (opcional)
  if (-not $SkipNormalize) {
    $pyArgs = @(".\normalizar_titulos_pasta.py", "--lote", $Lote)
    Invoke-Step "2) Normalizar títulos do lote" $pyArgs

  } else {
    Write-Host "`n(2) Normalização pulada." -ForegroundColor DarkYellow
  }

  # 3) Consolidar em SÉRIE (opcional)
  if (-not $SkipConsolidate) {
    $pyArgs = @(".\consolidar_serie_por_esboco.py", "--lote", $Lote, "--threshold", "$Threshold")
    if ($ContinueSeries) { $pyArgs += "--continue-series" }
    Invoke-Step "3) Consolidar lote em SÉRIE" $pyArgs

  } else {
    Write-Host "`n(3) Consolidação pulada." -ForegroundColor DarkYellow
  }

  # Descobre série via .last_series.txt (gerada pela consolidação)
  $SerieRaw = Read-LastSeries $ScriptsDir
  $Serie    = Resolve-SeriesName $SerieRaw
  Write-Host ">> Série resolvida: $Serie" -ForegroundColor Yellow

  if (-not $Serie) {
    Write-Host "`n⚠️  Não encontrei .last_series.txt. Se você pulou consolidação, isso é esperado." -ForegroundColor DarkYellow
  } else {
    Write-Host ">> SÉRIE atual (.last_series.txt): $Serie" -ForegroundColor Yellow
  }

  # 4) PDFs (opcional)
  if (-not $SkipPDF) {
    if (-not $Serie) { throw "Não dá para gerar PDF sem nome de série (.last_series.txt). Rode a consolidação." }
    $pyArgs = @(".\converter_em_pdf_por_esboco.py", "--serie", $Serie)
    if ($OverwritePDF) { $pyArgs += "--overwrite" }
    if ($PdfLimit -gt 0) { $pyArgs += @("--limit", "$PdfLimit") }
    Invoke-Step "4) Converter em PDF por ESBOÇO" $pyArgs

  } else {
    Write-Host "`n(4) PDF pulado." -ForegroundColor DarkYellow
  }

  # 5) Prompts (opcional)
  if (-not $SkipPrompts) {
    if (-not $Serie) { throw "Não dá para gerar prompts sem nome de série (.last_series.txt)." }
    $pyArgs = @(".\gerar_prompts_imagens.py", "--series", $Serie, "--npar", "$NPar", "--maxchars", "$MaxChars")
    Invoke-Step "5) Gerar prompts de imagens" $pyArgs
  } else {
    Write-Host "`n(5) Prompts pulado." -ForegroundColor DarkYellow
  }

  Write-Host "`n✅ Pipeline concluído com sucesso." -ForegroundColor Green
}
finally {
  Pop-Location
}
