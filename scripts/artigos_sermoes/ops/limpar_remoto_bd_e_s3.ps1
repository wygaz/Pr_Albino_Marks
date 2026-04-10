param(
    [switch]$Execute,
    [switch]$KeepTaxonomy,
    [switch]$SkipS3
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
$ResetScript = Join-Path $ProjectRoot 'scripts\artigos_sermoes\ops\reset_publicacao_site.py'
$DbInfoScript = Join-Path $ProjectRoot 'scripts\artigos_sermoes\ops\db_url_info.py'
$env:ENV_NAME = 'remoto'
$env:PYTHONIOENCODING = 'utf-8'

Write-Host '[1/2] Limpando publicacao remota no banco/storage...' -ForegroundColor Yellow
$cmd = @($ResetScript)
if ($Execute) { $cmd += '--execute' }
if ($KeepTaxonomy) { $cmd += '--keep-taxonomy' }
& $PythonExe @cmd
if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha na limpeza remota do banco/storage.' }

if (-not $SkipS3) {
    $DbInfo = & $PythonExe $DbInfoScript --env-name remoto --field json | ConvertFrom-Json
    if ($DbInfo.use_s3 -and $DbInfo.bucket) {
        $Aws = Get-Command aws -ErrorAction SilentlyContinue
        if (-not $Aws) { throw 'aws cli nao encontrado no PATH para limpeza do S3.' }
        Write-Host '[2/2] Limpando prefixos de publicacao no S3 remoto...' -ForegroundColor Yellow
        $prefixes = @(
            'uploads/artigos/',
            'pdfs/artigos/',
            'imagens/artigos/',
            'pdfs/sermoes/',
            'pdfs/relatorios_tecnicos/',
            'docs/sermoes/',
            'imagens/sermoes/'
        )
        foreach ($prefix in $prefixes) {
            if ($Execute) {
                aws s3 rm "s3://$($DbInfo.bucket)/$prefix" --recursive
                if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha ao limpar prefixo S3: $prefix" }
            }
            else {
                Write-Host "[DRY] aws s3 rm s3://$($DbInfo.bucket)/$prefix --recursive"
            }
        }
    }
    else {
        Write-Host '[2/2] Perfil remoto sem S3 ativo. Etapa ignorada.' -ForegroundColor DarkYellow
    }
}
else {
    Write-Host '[2/2] Limpeza do S3 ignorada por -SkipS3.' -ForegroundColor DarkYellow
}

if (-not $Execute) {
    Write-Host '[INFO] Nada foi apagado. Rode novamente com -Execute para aplicar.' -ForegroundColor DarkYellow
}
else {
    Write-Host '[OK] Limpeza remota concluida.' -ForegroundColor Green
}
