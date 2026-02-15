param(
  # SeguranÃ§a: por padrÃ£o, exige que db_check.py mostre HOST local.
  [switch]$AllowRemote,

  # Se quiser forÃ§ar um nome de DB (caso seu db_check.py nÃ£o exista):
  [string]$DbName = "",

  # UsuÃ¡rio do Postgres local (default: postgres)
  [string]$PgUser = "postgres",

  # ExecutÃ¡vel python
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

$RepoRoot = Find-RepoRoot $PSScriptRoot
if (-not $RepoRoot) { throw "NÃ£o encontrei manage.py/.git." }

$dbCheck = Join-Path $RepoRoot "tools\db_check.py"

$dbHost = ""
$dbNameFound = ""

if (Test-Path $dbCheck) {
  Write-Host "\n=== DB CHECK (anti-desastre) ===" -ForegroundColor Cyan
  $env:ENV_NAME = "local"
  $out = & $PythonExe $dbCheck 2>&1
  $out | ForEach-Object { Write-Host $_ }

  $hostLine = ($out | Select-String -Pattern '^HOST\s*=\s*(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1)
  $nameLine = ($out | Select-String -Pattern '^NAME\s*=\s*(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1)

  if ($hostLine) { $dbHost = $hostLine.Matches[0].Groups[1].Value.Trim() }
  if ($nameLine) { $dbNameFound = $nameLine.Matches[0].Groups[1].Value.Trim() }
}

if (-not $DbName) {
  $DbName = $dbNameFound
}

if (-not $DbName) {
  throw "NÃ£o consegui descobrir o nome do banco. Passe -DbName 'SEU_DB'."
}

$isLocal = ($dbHost -match 'localhost') -or ($dbHost -match '127\.0\.0\.1') -or (-not $dbHost)
if (-not $isLocal -and -not $AllowRemote) {
  throw "ABORTADO: HOST do BD nÃ£o parece local ('$dbHost'). NÃ£o vou dropar. Se vocÃª realmente quer rodar no remoto, use -AllowRemote." 
}

Write-Host "\n=== RESET DB UTF-8 (uma Ãºnica vez) ===" -ForegroundColor Cyan
Write-Host "DB: $DbName" -ForegroundColor Yellow

# DROP + CREATE UTF8 (template0 garante encoding)
# (Opcional, mas ajuda quando o DB está em uso)
$DbNameSafe = $DbName.Replace("'", "''")
$killSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DbNameSafe' AND pid <> pg_backend_pid();"
psql -U $PgUser -d postgres -c $killSql | Out-Null

# DROP + CREATE UTF8 (template0 garante encoding) — sem \" (PowerShell não usa backslash para escapar aspas)
$dropSql   = 'DROP DATABASE IF EXISTS "{0}";' -f $DbName
$createSql = 'CREATE DATABASE "{0}" WITH ENCODING ''UTF8'' TEMPLATE template0;' -f $DbName

psql -U $PgUser -d postgres -c $dropSql
psql -U $PgUser -d postgres -c $createSql

Write-Host "`nVerificando encoding..." -ForegroundColor Cyan
psql -U $PgUser -d $DbName -c "SHOW server_encoding;"

Write-Host "\nAgora rode: python manage.py migrate" -ForegroundColor Green

