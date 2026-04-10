# Pr_Albino_Marks_restaurado\atualizar_zips_generico.ps1
#Requires -Version 5.1

param(
  [string]$Root,
  [string]$Config = "",

  [switch]$InitConfig,

  # Atualiza o ZIP original (sem criar ZIP com timestamp)
  [switch]$InPlace,

  # Só substitui arquivo se o da origem for mais novo que o que está no ZIP
  [switch]$OnlyNewer,

  # Se quiser garantir por conteúdo (mais lento):
  # none | sha256 | md5
  [ValidateSet("none","sha256","md5")]
  [string]$Hash = "none",

  # Apenas simula (não grava ZIP)
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest




# ---------- Encoding (evita prompt "diretÃ³rio" etc.) ----------
try {
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  [Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
} catch {}

# ---------- Helpers ----------
function Resolve-PathSafe {
  param([string]$p)
  if ([string]::IsNullOrWhiteSpace($p)) { return $null }
  $p = $p.Trim()
  $p = $p.Trim('"').Trim("'")
  $p = $p -replace '/', '\'
  try { return (Resolve-Path -LiteralPath $p -ErrorAction Stop).Path } catch { return $p }
}

function Resolve-UnderRoot {
  param([string]$root, [string]$p)
  $p = Resolve-PathSafe $p
  if ([string]::IsNullOrWhiteSpace($p)) { return $null }
  if ([System.IO.Path]::IsPathRooted($p)) { return $p }
  return (Join-Path $root $p)
}

function New-EmptyMirrorTree {
  param([string]$fromDir, [string]$toDir)

  Get-ChildItem -Path $fromDir -Directory -Recurse | ForEach-Object {
    $rel  = $_.FullName.Substring($fromDir.Length).TrimStart("\")
    $dest = Join-Path $toDir $rel
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
  }
}

function Get-HashIfNeeded {
  param([string]$path, [string]$algo)
  if ($algo -eq "none") { return $null }
  return (Get-FileHash -LiteralPath $path -Algorithm $algo).Hash
}

function Find-FileInSources {
  param(
    [string]$relativePath,
    [string[]]$sources,
    [string[]]$ignoreDirs
  )

  # 1) tentativa direta: src + relativePath
  foreach ($s in $sources) {
    $cand = Join-Path $s $relativePath
    if (Test-Path $cand -PathType Leaf) { return $cand }
  }

  # 2) fallback: procurar por nome (mais caro)
  $leaf = Split-Path $relativePath -Leaf

  foreach ($s in $sources) {
    $exclude = @()
    foreach ($d in $ignoreDirs) { $exclude += (Join-Path $s $d) }

    $found = Get-ChildItem -Path $s -Recurse -File -Filter $leaf -ErrorAction SilentlyContinue |
      Where-Object {
        $ok = $true
        foreach ($ex in $exclude) {
          if ($_.FullName.StartsWith($ex, [System.StringComparison]::OrdinalIgnoreCase)) {
            $ok = $false; break
          }
        }
        $ok
      } |
      Select-Object -First 1

    if ($found) { return $found.FullName }
  }

  return $null
}

function Make-ZipNameWithTimestamp {
  param([string]$zipFolder, [string]$prefix)
  $stamp = (Get-Date).ToString("dd-MM-yyyy_HH'h'mm")
  return (Join-Path $zipFolder ("{0}{1}.zip" -f $prefix, $stamp))
}

# ---------- Paths ----------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($Config)) {
  $Config = Join-Path $ScriptDir "zip_jobs.json"
} else {
  $Config = Resolve-PathSafe $Config
}

if ($InitConfig) {
  $sample = @{
    ignore_dirs = @(".git","venv",".venv","__pycache__","node_modules","Apenas_Local")
    jobs = @(
      @{
        name = "pralbinomarks"
        zip  = "A_Lei_no_NT\Zip\pralbinomarks_erm_11-02-2026.zip"
        output_prefix = "pralbinomarks_em_"
        sources = @("pralbinomarks")
      },
      @{
        name = "raiz+app"
        zip  = "A_Lei_no_NT\Zip\Raiz_e_arqs_do_Projeto_em_11-02-2026.zip"
        output_prefix = "Raiz_e_arqs_do_Projeto_em_"
        sources = @(".")
      },
      @{
        name = "templates"
        zip  = "A_Lei_no_NT\Zip\templates_Pr_Albino_em_11-02-2026.zip"
        output_prefix = "templates_Pr_Albino_em_"
        sources = @("pralbinomarks","A_Lei_no_NT")
      }
    )
  } | ConvertTo-Json -Depth 8

  $sample | Out-File -FilePath $Config -Encoding UTF8
  Write-Host "OK. Config criada em: $Config"
  Write-Host "Edite o JSON e depois rode: .\atualizar_zips_generico.ps1 -Root ""C:\...\Pr_Albino_Marks_restaurado"""
  exit 0
}

if (!(Test-Path $Config -PathType Leaf)) {
  throw "Config not found: $Config. Tip: run .\atualizar_zips_generico.ps1 -InitConfig"
}

if ([string]::IsNullOrWhiteSpace($Root)) {
  $Root = Read-Host "Type the project root folder (ex.: C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado)"
}
$Root = Resolve-PathSafe $Root
if ([string]::IsNullOrWhiteSpace($Root)) { throw "Root folder not provided." }
if (!(Test-Path $Root -PathType Container)) { throw "Root folder does not exist: $Root" }

# ---------- Load config ----------
$cfg = Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
$IgnoreDirs = @(".git","venv",".venv","__pycache__","node_modules","Apenas_Local")
if ($cfg.ignore_dirs) { $IgnoreDirs = @($cfg.ignore_dirs) }

if (-not $cfg.jobs -or $cfg.jobs.Count -eq 0) {
  throw "No jobs found in config: $Config"
}

# staging
$zipDirDefault = Join-Path $Root "A_Lei_no_NT\Zip"
$stagingBase = Join-Path $zipDirDefault "_temp_update"
New-Item -ItemType Directory -Force -Path $stagingBase | Out-Null

foreach ($job in $cfg.jobs) {
  $name   = $job.name
  $zipRel = $job.zip
  $prefix = $job.output_prefix

  if ([string]::IsNullOrWhiteSpace($name))   { throw "Job missing 'name'." }
  if ([string]::IsNullOrWhiteSpace($zipRel)) { throw "Job '$name' missing 'zip'." }
  if (-not $job.sources -or $job.sources.Count -eq 0) { throw "Job '$name' missing 'sources'." }

  $zipPath = Resolve-UnderRoot $Root $zipRel
  if (!(Test-Path $zipPath -PathType Leaf)) { throw "ZIP not found: $zipPath" }

  $zipFolder = Split-Path $zipPath -Parent

  $sources = @()
  foreach ($s in $job.sources) {
    $s2 = Resolve-UnderRoot $Root $s
    if (!(Test-Path $s2 -PathType Container)) { throw "Source not found: $s2" }
    $sources += $s2
  }

  Write-Host ""
  Write-Host "==============================="
  Write-Host "JOB: $name"
  Write-Host "ZIP: $zipPath"
  Write-Host "Sources: $($sources -join ' | ')"
  Write-Host "OnlyNewer: $OnlyNewer  |  InPlace: $InPlace  |  Hash: $Hash  |  DryRun: $DryRun"
  Write-Host "==============================="

  $stageOriginal = Join-Path $stagingBase ($name + "_orig")
  $stageTemp     = Join-Path $stagingBase ($name + "_temp")

  if (Test-Path $stageOriginal) { Remove-Item $stageOriginal -Recurse -Force }
  if (Test-Path $stageTemp)     { Remove-Item $stageTemp -Recurse -Force }

  New-Item -ItemType Directory -Force -Path $stageOriginal | Out-Null
  New-Item -ItemType Directory -Force -Path $stageTemp     | Out-Null

  Write-Host "1) Extracting ZIP..."
  Expand-Archive -Path $zipPath -DestinationPath $stageOriginal -Force

  Write-Host "2) Mirroring folder structure..."
  New-EmptyMirrorTree -fromDir $stageOriginal -toDir $stageTemp

  Write-Host "3) Copying updated files to temp (only files that exist in the ZIP)..."
  $files = Get-ChildItem -Path $stageOriginal -Recurse -File

  $missing = New-Object System.Collections.Generic.List[string]
  $kept    = 0
  $updated = 0

  foreach ($f in $files) {
    $rel = $f.FullName.Substring($stageOriginal.Length).TrimStart("\")

    $srcFile = Find-FileInSources -relativePath $rel -sources $sources -ignoreDirs $IgnoreDirs
    $destFile = Join-Path $stageTemp $rel
    $destDir  = Split-Path $destFile -Parent
    if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }

    $useSrc = $false
    if ($srcFile) {
      $useSrc = $true

      if ($OnlyNewer) {
        $srcInfo  = Get-Item -LiteralPath $srcFile
        $zipInfo  = Get-Item -LiteralPath $f.FullName

        if ($srcInfo.LastWriteTimeUtc -le $zipInfo.LastWriteTimeUtc) {
          # pode ser que o conteúdo esteja diferente mas a data não
          if ($Hash -ne "none") {
            $h1 = Get-HashIfNeeded -path $srcFile   -algo $Hash
            $h2 = Get-HashIfNeeded -path $f.FullName -algo $Hash
            if ($h1 -eq $h2) { $useSrc = $false } else { $useSrc = $true }
          } else {
            $useSrc = $false
          }
        }
      }
    }

    if ($useSrc) {
      if (-not $DryRun) { Copy-Item -LiteralPath $srcFile -Destination $destFile -Force }
      $updated++
    } elseif ($srcFile) {
      # encontrou, mas decidiu manter o do ZIP (OnlyNewer)
      if (-not $DryRun) { Copy-Item -LiteralPath $f.FullName -Destination $destFile -Force }
      $kept++
    } else {
      # não encontrou na(s) origem(ns): mantém o original do ZIP
      if (-not $DryRun) { Copy-Item -LiteralPath $f.FullName -Destination $destFile -Force }
      $missing.Add($rel) | Out-Null
    }
  }

  if ($missing.Count -gt 0) {
    Write-Host "WARNING: Not found in sources (kept original from ZIP):"
    $missing | Select-Object -First 30 | ForEach-Object { Write-Host "  - $_" }
    if ($missing.Count -gt 30) { Write-Host "  ... +$($missing.Count-30) items" }
  } else {
    Write-Host "OK: All ZIP files were found in sources."
  }

  Write-Host "Stats: updated=$updated  kept=$kept  missing=$($missing.Count)  total=$($files.Count)"

  # 4) Recompactar
  $targetZip = $null
  if ($InPlace) {
    $targetZip = $zipPath
  } else {
    if ([string]::IsNullOrWhiteSpace($prefix)) {
      $prefix = ($name + "_")
    }
    $targetZip = Make-ZipNameWithTimestamp -zipFolder $zipFolder -prefix $prefix
  }

  Write-Host "4) Repacking..."
  if ($DryRun) {
    Write-Host "DRY-RUN: would write ZIP => $targetZip"
  } else {
    $tmpZip = Join-Path $zipFolder ("._tmp_" + [System.Guid]::NewGuid().ToString("N") + ".zip")
    if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }

    Compress-Archive -Path (Join-Path $stageTemp "*") -DestinationPath $tmpZip -Force

    if ($InPlace) {
      # troca atômica
      Move-Item -LiteralPath $tmpZip -Destination $zipPath -Force
      Write-Host "OK. ZIP updated in place: $zipPath"
    } else {
      Move-Item -LiteralPath $tmpZip -Destination $targetZip -Force
      Write-Host "OK. New ZIP created: $targetZip"
    }
  }
}

Write-Host ""
Write-Host "All packages processed."
