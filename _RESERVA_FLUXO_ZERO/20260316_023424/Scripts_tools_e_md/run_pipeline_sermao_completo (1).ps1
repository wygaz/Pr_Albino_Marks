param(
    [Parameter(Mandatory = $true)]
    [string]$Docx,

    [Parameter(Mandatory = $true)]
    [string]$Serie,

    [string]$Titulo = "",
    [string]$Resumo = "Sermão publicado pelo pipeline local.",
    [int]$Ordem = 0,
    [switch]$Visivel,

    [string]$Model = "gpt-5",
    [int]$MaxChars = 60000,

    [string]$RelatoriosOutDir = ".\Apenas_Local\RELATORIOS_TECNICOS",
    [string]$SermoesOutDir = ".\Apenas_Local\SERMOES_GERADOS",
    [string]$FormatadosOutDir = ".\Apenas_Local\SERMOES_FORMATADOS"
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathText, [string]$BaseDir) {
    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return [System.IO.Path]::GetFullPath($PathText)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathText))
}

function Assert-FileExists([string]$PathText, [string]$Label) {
    if (-not (Test-Path -LiteralPath $PathText -PathType Leaf)) {
        throw "[ERRO] Arquivo não encontrado em $Label: $PathText"
    }
}

function Assert-Dir([string]$PathText) {
    if (-not (Test-Path -LiteralPath $PathText -PathType Container)) {
        New-Item -ItemType Directory -Path $PathText -Force | Out-Null
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\.."))
Set-Location $ProjectRoot

$DocxAbs = Resolve-AbsolutePath $Docx $ProjectRoot
Assert-FileExists $DocxAbs "-Docx"

$RelatoriosAbs = Resolve-AbsolutePath $RelatoriosOutDir $ProjectRoot
$SermoesAbs = Resolve-AbsolutePath $SermoesOutDir $ProjectRoot
$FormatadosAbs = Resolve-AbsolutePath $FormatadosOutDir $ProjectRoot

Assert-Dir $RelatoriosAbs
Assert-Dir $SermoesAbs
Assert-Dir $FormatadosAbs

$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($DocxAbs)
if ([string]::IsNullOrWhiteSpace($Titulo)) {
    $Titulo = $BaseName
}

$RelatorioMd = Join-Path $RelatoriosAbs ("{0}__relatorio_tecnico__{1}.md" -f $BaseName, $Model)
$SermaoMd = Join-Path $SermoesAbs ("{0}__relatorio_tecnico__{1}__sermao__{1}.md" -f $BaseName, $Model)
$HtmlA4 = Join-Path $FormatadosAbs ("{0}__relatorio_tecnico__{1}__sermao__{1}__A4.html" -f $BaseName, $Model)
$HtmlA5 = Join-Path $FormatadosAbs ("{0}__relatorio_tecnico__{1}__sermao__{1}__A5.html" -f $BaseName, $Model)
$HtmlTablet = Join-Path $FormatadosAbs ("{0}__relatorio_tecnico__{1}__sermao__{1}__tablet.html" -f $BaseName, $Model)
$DocxA4 = Join-Path $FormatadosAbs ("{0}__relatorio_tecnico__{1}__sermao__{1}__A4.docx" -f $BaseName, $Model)

Write-Host "[1/4] Gerando relatório técnico..." -ForegroundColor Cyan
& python .\gerar_relatorio_tecnico_de_docx.py `
    --docx $DocxAbs `
    --outdir $RelatoriosAbs `
    --model $Model `
    --max-chars $MaxChars
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na geração do relatório técnico." }
Assert-FileExists $RelatorioMd "relatório técnico"

Write-Host "[2/4] Gerando sermão a partir do relatório..." -ForegroundColor Cyan
& python .\gerar_sermao_de_relatorio.py `
    --relatorio $RelatorioMd `
    --outdir $SermoesAbs `
    --model $Model
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na geração do sermão." }
Assert-FileExists $SermaoMd "sermão em Markdown"

Write-Host "[3/4] Exportando formatos finais..." -ForegroundColor Cyan
& python .\exportar_formatos_sermao_md.py `
    --md $SermaoMd `
    --outdir $FormatadosAbs
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na exportação dos formatos do sermão." }
Assert-FileExists $HtmlA4 "HTML A4"
Assert-FileExists $HtmlA5 "HTML A5"
Assert-FileExists $HtmlTablet "HTML Tablet"
Assert-FileExists $DocxA4 "DOCX A4"

Write-Host "[4/4] Publicando no app 'sermoes'..." -ForegroundColor Cyan
$PublishArgs = @(
    '.\scripts\publicacao\pipeline_publicar_sermao.py',
    '--titulo', $Titulo,
    '--serie', $Serie,
    '--resumo', $Resumo,
    '--ordem', $Ordem,
    '--html-a4', $HtmlA4,
    '--html-a5', $HtmlA5,
    '--html-tablet', $HtmlTablet,
    '--docx-a4', $DocxA4
)

if ($Visivel) {
    $PublishArgs += '--visivel'
}

& python @PublishArgs
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na publicação do sermão no Django." }

Write-Host ""
Write-Host "[OK] Pipeline completo concluído com sucesso." -ForegroundColor Green
Write-Host "     DOCX origem : $DocxAbs"
Write-Host "     Título      : $Titulo"
Write-Host "     Série       : $Serie"
Write-Host "     Relatório   : $RelatorioMd"
Write-Host "     Sermão MD   : $SermaoMd"
Write-Host "     HTML A4     : $HtmlA4"
Write-Host "     HTML A5     : $HtmlA5"
Write-Host "     HTML Tablet : $HtmlTablet"
Write-Host "     DOCX A4     : $DocxA4"
