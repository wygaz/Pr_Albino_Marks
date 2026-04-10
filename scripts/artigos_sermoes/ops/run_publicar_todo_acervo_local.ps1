param(
    [switch]$ExecuteReset,
    [switch]$OverwriteMedia,
    [int]$LimitSermoes = 0,
    [string]$PythonExe = "",
    [string]$SeriesRoot = ".\Apenas_Local\operacional\artigos\series",
    [string]$PdfRoot = ".\Apenas_Local\operacional\artigos\pdfs",
    [string]$ImgRoot = ".\Apenas_Local\operacional\artigos\imagens",
    [string]$SermoesFormatadosRoot = ".\Apenas_Local\operacional\sermoes\formatados",
    [string]$DossiesFormatadosRoot = ".\Apenas_Local\operacional\dossies\formatados"
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

function Resolve-AbsolutePath([string]$PathText, [string]$BaseDir) {
    if ([System.IO.Path]::IsPathRooted($PathText)) { return [System.IO.Path]::GetFullPath($PathText) }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathText))
}

function Resolve-ScriptFile([string]$ProjectRoot, [string[]]$Candidates) {
    foreach ($rel in $Candidates) {
        $full = Join-Path $ProjectRoot $rel
        if (Test-Path -LiteralPath $full -PathType Leaf) { return $full }
    }
    throw "Script nao encontrado. Candidatos: $($Candidates -join '; ')"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Get-ProjectRoot $ScriptDir
Set-Location $ProjectRoot

if (-not $PythonExe) {
    $VenvPy = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
    $PythonExe = if (Test-Path $VenvPy) { $VenvPy } else { 'python' }
}

$env:ENV_NAME = 'local'
$env:PYTHONIOENCODING = 'utf-8'

$ResetScript = Resolve-ScriptFile $ProjectRoot @('scripts\artigos_sermoes\ops\reset_publicacao_site.py')
$PublishArticles = Resolve-ScriptFile $ProjectRoot @(
    'scripts\artigos_sermoes\publicar_artigos_operacional.py',
    'scripts\homologacao\pipeline\publicar_artigos_operacional.py'
)
$PublishSermon = Resolve-ScriptFile $ProjectRoot @(
    'scripts\artigos_sermoes\pipeline_publicar_sermao.py',
    'scripts\homologacao\pipeline\pipeline_publicar_sermao.py'
)
$BatchPublishSermons = Resolve-ScriptFile $ProjectRoot @('scripts\artigos_sermoes\ops\publicar_sermoes_lote.py')

if ($ExecuteReset) {
    Write-Host '[0/3] Limpando publicacao local...' -ForegroundColor Yellow
    & $PythonExe $ResetScript --execute
    if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha no reset da publicacao local.' }
}

Write-Host '[1/3] Publicando artigos no site local...' -ForegroundColor Cyan
$articleCmd = @($PublishArticles, '--series-root', (Resolve-AbsolutePath $SeriesRoot $ProjectRoot), '--pdf-root', (Resolve-AbsolutePath $PdfRoot $ProjectRoot), '--img-root', (Resolve-AbsolutePath $ImgRoot $ProjectRoot))
if ($OverwriteMedia) { $articleCmd += '--overwrite-media' }
& $PythonExe @articleCmd
if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha na publicacao dos artigos.' }

Write-Host '[2/3] Publicando sermoes no site local...' -ForegroundColor Cyan
$sermonCmd = @(
    $BatchPublishSermons,
    '--publish-script', $PublishSermon,
    '--sermoes-formatados-root', (Resolve-AbsolutePath $SermoesFormatadosRoot $ProjectRoot),
    '--dossies-formatados-root', (Resolve-AbsolutePath $DossiesFormatadosRoot $ProjectRoot)
)
if ($LimitSermoes -gt 0) { $sermonCmd += @('--limit', "$LimitSermoes") }
& $PythonExe @sermonCmd
if ($LASTEXITCODE -ne 0) { throw '[ERRO] Falha na publicacao dos sermoes.' }

Write-Host '[3/3] Concluido. Recarregue o acervo local.' -ForegroundColor Green
