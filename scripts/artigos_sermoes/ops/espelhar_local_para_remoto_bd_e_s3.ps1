param(
    [string]$BackupBase = ".\Apenas_Local\backups\espelhamento",
    [switch]$SkipS3,
    [switch]$FullDatabase,
    [switch]$ExecuteResetRemote
)

$ErrorActionPreference = 'Stop'

function Get-ProjectRoot([string]$StartDir) {
    $cur = [System.IO.Path]::GetFullPath($StartDir)
    for ($i = 0; $i -lt 12; $i++) {
        if ((Test-Path (Join-Path $cur 'manage.py')) -or (Test-Path (Join-Path $cur '.git'))) { return $cur }
        $parent = Split-Path -Parent $cur
        if (-not $parent -or $parent -eq $cur) { break }
        $cur = $parent
    }
    throw 'Raiz do projeto nao encontrada.'
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Get-ProjectRoot $ScriptDir
Set-Location $ProjectRoot
$PythonExe = if (Test-Path (Join-Path $ProjectRoot 'venv\Scripts\python.exe')) { Join-Path $ProjectRoot 'venv\Scripts\python.exe' } else { 'python' }
$DumpScript = Join-Path $ProjectRoot 'scripts\artigos_sermoes\ops\dump_publicacao_site.py'
$ResetScript = Join-Path $ProjectRoot 'scripts\artigos_sermoes\ops\reset_publicacao_site.py'
$DbInfoScript = Join-Path $ProjectRoot 'scripts\artigos_sermoes\ops\db_url_info.py'
$env:PYTHONIOENCODING = 'utf-8'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BaseOut = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $BackupBase))
$RunDir = Join-Path $BaseOut $stamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

Write-Host '[1/4] Gerando fixture da publicacao local...' -ForegroundColor Cyan
$env:ENV_NAME = 'local'
& $PythonExe $DumpScript --output-dir $RunDir --label local --filename 'publicacao_local.json'
if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no dump local.' }
$Fixture = Join-Path $RunDir 'publicacao_local.json'

if ($FullDatabase) {
    $Local = & $PythonExe $DbInfoScript --env-name local --field json | ConvertFrom-Json
    $Remote = & $PythonExe $DbInfoScript --env-name remoto --field json | ConvertFrom-Json
    $PgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
    $PgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
    if (-not $PgDump -or -not $PgRestore) { throw 'pg_dump/pg_restore nao encontrados no PATH para espelhamento full.' }

    Write-Host '[2/4] Espelhando banco local -> remoto via pg_dump/pg_restore...' -ForegroundColor Cyan
    $DumpFile = Join-Path $RunDir 'local_full.dump'
    $env:PGHOST = $Local.host; $env:PGPORT = $Local.port; $env:PGUSER = $Local.user; $env:PGPASSWORD = $Local.password; $env:PGDATABASE = $Local.database
    pg_dump --format=custom --no-owner --no-privileges --file $DumpFile
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no pg_dump local.' }

    $env:PGHOST = $Remote.host; $env:PGPORT = $Remote.port; $env:PGUSER = $Remote.user; $env:PGPASSWORD = $Remote.password; $env:PGDATABASE = $Remote.database
    pg_restore --clean --if-exists --no-owner --no-privileges --single-transaction -d $Remote.database $DumpFile
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no pg_restore remoto.' }
}
else {
    Write-Host '[2/4] Limpando publicacao remota e importando fixture local...' -ForegroundColor Cyan
    $env:ENV_NAME = 'remoto'
    $resetArgs = @($ResetScript, '--execute')
    & $PythonExe @resetArgs
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha na limpeza remota antes do espelhamento.' }
    & $PythonExe .\manage.py loaddata $Fixture
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no loaddata remoto.' }
}

if (-not $SkipS3) {
    Write-Host '[3/4] Espelhando media local para o S3 remoto...' -ForegroundColor Cyan
    $Remote = & $PythonExe $DbInfoScript --env-name remoto --field json | ConvertFrom-Json
    if ($Remote.use_s3 -and $Remote.bucket) {
        $Aws = Get-Command aws -ErrorAction SilentlyContinue
        if (-not $Aws) { throw 'aws cli nao encontrado no PATH para sync com S3.' }
        $LocalMedia = Join-Path $ProjectRoot 'media'
        if (-not (Test-Path -LiteralPath $LocalMedia -PathType Container)) {
            throw "Pasta media local nao encontrada: $LocalMedia"
        }
        aws s3 sync $LocalMedia "s3://$($Remote.bucket)" --delete
        if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no espelhamento do media local para o S3 remoto.' }
    }
    else {
        Write-Host '[3/4] Perfil remoto sem S3 ativo. Etapa ignorada.' -ForegroundColor DarkYellow
    }
}
else {
    Write-Host '[3/4] Sync para S3 ignorado por -SkipS3.' -ForegroundColor DarkYellow
}

Write-Host '[4/4] Espelhamento concluido.' -ForegroundColor Green
Write-Host "Artefatos desta execucao: $RunDir"
