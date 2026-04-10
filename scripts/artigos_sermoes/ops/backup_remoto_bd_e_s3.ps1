param(
    [string]$OutputDir = ".\Apenas_Local\backups\remoto",
    [switch]$FullDatabase
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

function Resolve-ScriptFile([string]$ProjectRoot, [string]$RelPath) {
    $full = Join-Path $ProjectRoot $RelPath
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Script nao encontrado: $full" }
    return $full
}

function Parse-EnvFile([string]$Path) {
    $data = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $data }
    foreach ($raw in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        if ($line.ToLower().StartsWith('export ')) { $line = $line.Substring(7).Trim() }
        $idx = $line.IndexOf('=')
        if ($idx -lt 1) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $data[$key] = $value
    }
    return $data
}

function Get-RemoteDbInfo([string]$ProjectRoot) {
    $envPath = Join-Path $ProjectRoot '.env.remoto'
    $envData = Parse-EnvFile $envPath
    $dbUrl = $envData['DATABASE_URL']
    if (-not $dbUrl) { $dbUrl = $envData['DATABASE_PUBLIC_URL'] }
    if (-not $dbUrl) { throw "DATABASE_URL nao encontrado em $envPath" }
    $uri = [System.Uri]$dbUrl
    $userInfo = $uri.UserInfo.Split(':', 2)
    $query = @{}
    $queryRaw = $uri.Query.TrimStart('?')
    if ($queryRaw) {
        foreach ($pair in $queryRaw.Split('&')) {
            if (-not $pair) { continue }
            $chunks = $pair.Split('=', 2)
            $qKey = [System.Uri]::UnescapeDataString($chunks[0])
            $qVal = if ($chunks.Count -gt 1) { [System.Uri]::UnescapeDataString($chunks[1]) } else { '' }
            $query[$qKey] = $qVal
        }
    }
    $useS3Value = $envData['USE_S3']
    if (-not $useS3Value) { $useS3Value = $envData['USE_S3_FOR_MEDIA'] }
    if (-not $useS3Value) { $useS3Value = '0' }
    return @{
        env_name = 'remoto'
        env_path = $envPath
        database_url = $dbUrl
        host = $uri.Host
        port = if ($uri.Port -gt 0) { [string]$uri.Port } else { '5432' }
        database = $uri.AbsolutePath.TrimStart('/')
        user = [System.Uri]::UnescapeDataString($userInfo[0])
        password = if ($userInfo.Count -gt 1) { [System.Uri]::UnescapeDataString($userInfo[1]) } else { '' }
        sslmode = $query['sslmode']
        bucket = if ($envData['S3_BUCKET_NAME']) { $envData['S3_BUCKET_NAME'] } else { $envData['AWS_STORAGE_BUCKET_NAME'] }
        use_s3 = @('1','true','yes') -contains $useS3Value.ToString().Trim().ToLower()
        aws_profile = $envData['AWS_PROFILE']
        aws_region = if ($envData['AWS_DEFAULT_REGION']) { $envData['AWS_DEFAULT_REGION'] } else { $envData['AWS_S3_REGION_NAME'] }
        aws_access_key_id = $envData['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = $envData['AWS_SECRET_ACCESS_KEY']
    }
}

function Resolve-PgDump() {
    $preferred = @(
        'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe',
        'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe'
    )
    foreach ($candidate in $preferred) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    $cmd = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw 'pg_dump nao encontrado no PATH nem nas instalacoes locais conhecidas.'
}

function Resolve-AwsCaBundle([string]$ProjectRoot) {
    # Em algumas maquinas o AWS CLI nao confia na cadeia local por padrao.
    # Quando houver um CA bundle valido, usamos de forma opcional sem acoplar
    # o script a um caminho fixo nem expor configuracoes sensiveis.
    if ($env:AWS_CA_BUNDLE) {
        $fromEnv = [System.IO.Path]::GetFullPath($env:AWS_CA_BUNDLE)
        if (Test-Path -LiteralPath $fromEnv -PathType Leaf) { return $fromEnv }
    }

    $venvCertifi = Join-Path $ProjectRoot 'venv\Lib\site-packages\certifi\cacert.pem'
    if (Test-Path -LiteralPath $venvCertifi -PathType Leaf) { return $venvCertifi }

    return $null
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Get-ProjectRoot $ScriptDir
Set-Location $ProjectRoot
$env:ENV_NAME = 'remoto'
$env:PYTHONIOENCODING = 'utf-8'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BaseOut = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputDir))
$RunDir = Join-Path $BaseOut $stamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

Write-Host '[1/3] Gerando fixture JSON da publicacao remota...' -ForegroundColor Cyan
if (-not $FullDatabase) {
    $PythonExe = if (Test-Path (Join-Path $ProjectRoot 'venv\Scripts\python.exe')) { Join-Path $ProjectRoot 'venv\Scripts\python.exe' } else { 'python' }
    $DumpScript = Resolve-ScriptFile $ProjectRoot 'scripts\artigos_sermoes\ops\dump_publicacao_site.py'
    & $PythonExe $DumpScript --output-dir $RunDir --label remoto
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no dump JSON remoto.' }
}
else {
    Write-Host '[1/3] Dump JSON remoto ignorado em modo -FullDatabase.' -ForegroundColor DarkYellow
}

$DbInfo = Get-RemoteDbInfo $ProjectRoot
if ($FullDatabase) {
    $PgDump = Resolve-PgDump
    Write-Host '[2/3] Gerando backup full do PostgreSQL remoto...' -ForegroundColor Cyan
    Write-Host "[INFO] pg_dump: $PgDump" -ForegroundColor DarkGray
    $env:PGHOST = $DbInfo.host
    $env:PGPORT = $DbInfo.port
    $env:PGUSER = $DbInfo.user
    $env:PGPASSWORD = $DbInfo.password
    $env:PGDATABASE = $DbInfo.database
    & $PgDump --format=custom --no-owner --no-privileges --file (Join-Path $RunDir 'remote_full.dump')
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no pg_dump remoto.' }
}
else {
    Write-Host '[2/3] Backup full do PostgreSQL remoto ignorado (use -FullDatabase para incluir).' -ForegroundColor DarkYellow
}

if ($DbInfo.use_s3 -and $DbInfo.bucket) {
    $Aws = Get-Command aws -ErrorAction SilentlyContinue
    if (-not $Aws) { throw 'aws cli nao encontrado no PATH para backup do S3.' }
    Write-Host '[3/3] Sincronizando bucket S3 remoto para backup local...' -ForegroundColor Cyan
    if ($DbInfo.aws_access_key_id) { $env:AWS_ACCESS_KEY_ID = $DbInfo.aws_access_key_id }
    if ($DbInfo.aws_secret_access_key) { $env:AWS_SECRET_ACCESS_KEY = $DbInfo.aws_secret_access_key }
    if ($DbInfo.aws_region) { $env:AWS_DEFAULT_REGION = $DbInfo.aws_region }
    $S3Dir = Join-Path $RunDir 's3'
    New-Item -ItemType Directory -Force -Path $S3Dir | Out-Null
    $AwsCaBundle = Resolve-AwsCaBundle $ProjectRoot
    if ($AwsCaBundle) {
        Write-Host "[INFO] Usando CA bundle para AWS CLI: $AwsCaBundle" -ForegroundColor DarkGray
        aws s3 sync "s3://$($DbInfo.bucket)" $S3Dir --ca-bundle $AwsCaBundle
    }
    else {
        aws s3 sync "s3://$($DbInfo.bucket)" $S3Dir
    }
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no backup do S3.' }
}
else {
    Write-Host '[3/3] Perfil remoto sem S3 ativo. Etapa ignorada.' -ForegroundColor DarkYellow
}

Write-Host "[OK] Backup remoto concluido em: $RunDir" -ForegroundColor Green
