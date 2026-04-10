# Pr_Albino_Marks_restaurado\atualizar_zips_Pr_Albino.ps1
#requires -Version 5.1
'''
1) Substituir os ZIPs originais no lugar + só copiar o que estiver mais novo
.\atualizar_zips.ps1 -InPlace -OnlyNewer

2) InPlace sem backup (não recomendo, mas disponível)
.\atualizar_zips.ps1 -InPlace -OnlyNewer -NoBackup
'''
param(
  [string]$Root = "",
  [string]$Config = ".\zip_jobs.json",
  [switch]$InitConfig,

  [switch]$InPlace,
  [switch]$OnlyNewer,
  [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

# --- Force UTF-8 output (helps accents on PS 5.1) ---
try {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [Console]::OutputEncoding = $utf8NoBom
  $OutputEncoding = $utf8NoBom
} catch {}

function Normalize-RootPath {
  param([string]$p)
  $p = $p.Trim().Trim('"')
  if ([string]::IsNullOrWhiteSpace($p)) { return $p }

  # Accept "\Users\..." (missing drive letter) -> assume SystemDrive
  if ($p -match '^[\\/](Users|Program Files|Windows|Temp)') {
    $p = Join-Path $env:SystemDrive $p.TrimStart("\", "/")
  }
  return $p
}

function Replace-RootToken {
  param([string]$s, [string]$root)
  if ($null -eq $s) { return $s }
  return $s.Replace("{root}", $root).Replace("{ROOT}", $root)
}

function Get-Stamp {
  return (Get-Date).ToString("dd-MM-yyyy_HH'h'mm")
}

function Make-ZipNameWithTimestamp {
  param([string]$zipFolder, [string]$prefix)
  $stamp = Get-Stamp
  return (Join-Path $zipFolder ("{0}{1}.zip" -f $prefix, $stamp))
}

function Make-BackupName {
  param([string]$zipPath)
  $dir  = Split-Path $zipPath -Parent
  $base = [IO.Path]::GetFileNameWithoutExtension($zipPath)
  $ext  = [IO.Path]::GetExtension($zipPath)
  $stamp = Get-Stamp
  return (Join-Path $dir ("{0}_bak_{1}{2}" -f $base, $stamp, $ext))
}

function New-EmptyMirrorTree {
  param([string]$fromDir, [string]$toDir)
  Get-ChildItem -Path $fromDir -Directory -Recurse | ForEach-Object {
    $rel  = $_.FullName.Substring($fromDir.Length).TrimStart("\")
    $dest = Join-Path $toDir $rel
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
  }
}

function Is-SilentMissing {
  param([string]$relativePath, [string[]]$patterns)
  foreach ($p in $patterns) {
    if ([string]::IsNullOrWhiteSpace($p)) { continue }
    if ($relativePath -like $p) { return $true }
  }
  return $false
}

function Resolve-ExistingSources {
  param([string[]]$sources)
  $ok = @()
  foreach ($s in $sources) {
    if ([string]::IsNullOrWhiteSpace($s)) { continue }
    if (Test-Path $s -PathType Container) { $ok += $s }
    else { Write-Host "   ! Source not found (ignored): $s" }
  }
  return $ok
}

function Find-FileInSources {
  param(
    [string]$relativePath,
    [string[]]$sources,
    [string[]]$ignoreDirs
  )

  # 1) Direct attempt: src + relativePath
  foreach ($s in $sources) {
    $cand = Join-Path $s $relativePath
    if (Test-Path $cand -PathType Leaf) { return $cand }
  }

  # 2) Fallback: search by filename
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

function Copy-FromSourceOrKeepOriginal {
  param(
    [string]$srcFile,
    [string]$origFile,
    [string]$destFile,
    [switch]$OnlyNewer
  )

  if (-not (Test-Path $srcFile -PathType Leaf)) {
    Copy-Item -Path $origFile -Destination $destFile -Force
    return $false
  }

  if ($OnlyNewer) {
    $srcInfo  = Get-Item $srcFile
    $origInfo = Get-Item $origFile

    # Copy only if source is newer than the file from ZIP
    if ($srcInfo.LastWriteTimeUtc -le $origInfo.LastWriteTimeUtc) {
      Copy-Item -Path $origFile -Destination $destFile -Force
      return $false
    }
  }

  Copy-Item -Path $srcFile -Destination $destFile -Force
  return $true
}

# ---------------------------
# Init sample config (optional)
# ---------------------------
if ($InitConfig) {
  $sample = @"
{
  "ignore_dirs": [".git", "venv", ".venv", "__pycache__", "node_modules", "Apenas_Local"],
  "silent_missing_patterns": ["*\\__pycache__\\*", "*.pyc"],

  "jobs": [
    {
      "name": "pralbinomarks",
      "zip": "{root}\\A_Lei_no_NT\\Zip\\pralbinomarks_erm_11-02-2026.zip",
      "prefix": "pralbinomarks_em_",
      "sources": ["{root}\\pralbinomarks"]
    },
    {
      "name": "raiz+app",
      "zip": "{root}\\A_Lei_no_NT\\Zip\\Raiz_e_arqs_do_Projeto_em_11-02-2026.zip",
      "prefix": "Raiz_e_arqs_do_Projeto_em_",
      "sources": ["{root}"]
    },
    {
      "name": "templates",
      "zip": "{root}\\A_Lei_no_NT\\Zip\\templates_Pr_Albino_em_11-02-2026.zip",
      "prefix": "templates_Pr_Albino_em_",
      "sources": ["{root}", "{root}\\pralbinomarks", "{root}\\A_Lei_no_NT"]
    }
  ]
}
"@
  Set-Content -Path $Config -Value $sample -Encoding UTF8
  Write-Host "Created sample config: $Config"
  exit 0
}

# ---------------------------
# Ask project root once
# ---------------------------
if ([string]::IsNullOrWhiteSpace($Root)) {
  $Root = Read-Host "Type the project root folder (ex.: C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado)"
}
$Root = Normalize-RootPath $Root

if ([string]::IsNullOrWhiteSpace($Root)) { throw "Root folder not provided." }
if (!(Test-Path $Root -PathType Container)) { throw "Root folder does not exist: $Root" }

# ---------------------------
# Load config
# ---------------------------
if (!(Test-Path $Config -PathType Leaf)) {
  throw "Config not found: $Config. Tip: run .\atualizar_zips.ps1 -InitConfig"
}

$cfgRaw = Get-Content -Path $Config -Raw -Encoding UTF8
$cfg = $cfgRaw | ConvertFrom-Json

$ignoreDirs = @()
if ($cfg.ignore_dirs) { $ignoreDirs = @($cfg.ignore_dirs) }

$silentMissing = @("*\__pycache__\*", "*.pyc")
if ($cfg.silent_missing_patterns) { $silentMissing = @($cfg.silent_missing_patterns) }

$jobs = @()
if ($cfg.jobs) { $jobs = @($cfg.jobs) }
if ($jobs.Count -eq 0) { throw "No jobs found in config: $Config" }

# Staging folder
$stagingBase = Join-Path (Split-Path $Config -Parent) "_temp_update"
if ([string]::IsNullOrWhiteSpace((Split-Path $Config -Parent))) {
  $stagingBase = ".\_temp_update"
}
New-Item -ItemType Directory -Force -Path $stagingBase | Out-Null

foreach ($job in $jobs) {
  $name    = $job.name
  $zipPath = Replace-RootToken -s $job.zip -root $Root
  $prefix  = $job.prefix

  $sourcesExpanded = @()
  foreach ($s in @($job.sources)) {
    $sourcesExpanded += (Replace-RootToken -s $s -root $Root)
  }
  $sources = Resolve-ExistingSources $sourcesExpanded

  if ([string]::IsNullOrWhiteSpace($name))    { throw "Job missing 'name'." }
  if ([string]::IsNullOrWhiteSpace($zipPath)) { throw "Job '$name' missing 'zip'." }
  if ([string]::IsNullOrWhiteSpace($prefix))  { throw "Job '$name' missing 'prefix'." }
  if (!(Test-Path $zipPath -PathType Leaf))   { throw "ZIP not found for job '$name': $zipPath" }
  if (!$sources -or $sources.Count -eq 0)     { throw "No valid sources for job '$name'." }

  $zipDir = Split-Path $zipPath -Parent

  Write-Host "`n==============================="
  Write-Host "JOB: $name"
  Write-Host "ZIP origin: $zipPath"
  Write-Host "Sources: $($sources -join ' | ')"
  Write-Host "Mode: InPlace=$InPlace  OnlyNewer=$OnlyNewer  Backup=$(-not $NoBackup)"
  Write-Host "==============================="

  # stage folders
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
  $copiedFromSource = 0
  $keptOriginal = 0

  foreach ($f in $files) {
    $rel = $f.FullName.Substring($stageOriginal.Length).TrimStart("\")
    $destFile = Join-Path $stageTemp $rel
    $destDir  = Split-Path $destFile -Parent
    if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }

    # silence missing for unwanted artifacts (pyc etc)
    if (Is-SilentMissing -relativePath $rel -patterns $silentMissing) {
      Copy-Item -Path $f.FullName -Destination $destFile -Force
      $keptOriginal++
      continue
    }

    $srcFile = Find-FileInSources -relativePath $rel -sources $sources -ignoreDirs $ignoreDirs
    if ($srcFile) {
      $didCopy = Copy-FromSourceOrKeepOriginal -srcFile $srcFile -origFile $f.FullName -destFile $destFile -OnlyNewer:$OnlyNewer
      if ($didCopy) { $copiedFromSource++ } else { $keptOriginal++ }
    } else {
      Copy-Item -Path $f.FullName -Destination $destFile -Force
      $missing.Add($rel) | Out-Null
      $keptOriginal++
    }
  }

  if ($missing.Count -gt 0) {
    Write-Host "   WARNING: Not found in sources (kept original from ZIP):"
    $missing | Select-Object -First 30 | ForEach-Object { Write-Host "     - $_" }
    if ($missing.Count -gt 30) { Write-Host "     ... +$($missing.Count-30) items" }
  } else {
    Write-Host "   OK: All ZIP files were found in sources."
  }

  Write-Host "   Summary: copied_from_source=$copiedFromSource  kept_original=$keptOriginal"

  Write-Host "4) Repacking..."
  $tempZip = Join-Path $stagingBase ($name + "_NEW.zip")
  if (Test-Path $tempZip) { Remove-Item $tempZip -Force }

  Compress-Archive -Path (Join-Path $stageTemp "*") -DestinationPath $tempZip -Force

  if ($InPlace) {
    if (-not $NoBackup) {
      $backupZip = Make-BackupName -zipPath $zipPath
      Copy-Item -Path $zipPath -Destination $backupZip -Force
      Write-Host "   Backup created: $backupZip"
    }

    Move-Item -Path $tempZip -Destination $zipPath -Force
    Write-Host "OK. ZIP overwritten in place: $zipPath"
  } else {
    $newZip = Make-ZipNameWithTimestamp -zipFolder $zipDir -prefix $prefix
    if (Test-Path $newZip) { Remove-Item $newZip -Force }
    Move-Item -Path $tempZip -Destination $newZip -Force
    Write-Host "OK. New ZIP created: $newZip"
  }
}

Write-Host "`nAll packages processed."
