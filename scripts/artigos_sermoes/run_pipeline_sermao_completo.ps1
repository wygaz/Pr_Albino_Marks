param(
    [Parameter(Mandatory = $true)]
    [string]$Docx,

    [Parameter(Mandatory = $true)]
    [string]$Serie,

    [string]$Titulo = "",
    [string]$Slug = "",
    [string]$Resumo = "Sermao publicado pelo pipeline local.",
    [int]$Ordem = 0,
    [switch]$Visivel,

    [string]$Model = "gpt-5",
    [int]$MaxChars = 60000,

    [string]$RelatoriosOutDir = ".\Apenas_Local\operacional\dossies\markdown",
    [string]$DossiesFormatadosOutDir = ".\Apenas_Local\operacional\dossies\formatados",
    [string]$SermoesOutDir = ".\Apenas_Local\operacional\sermoes\markdown",
    [string]$FormatadosOutDir = ".\Apenas_Local\operacional\sermoes\formatados"
)

$ErrorActionPreference = "Stop"

function Get-ProjectRoot([string]$StartDir) {
    $cur = [System.IO.Path]::GetFullPath($StartDir)
    for ($i = 0; $i -lt 10; $i++) {
        if ((Test-Path (Join-Path $cur "manage.py")) -or (Test-Path (Join-Path $cur ".git"))) {
            return $cur
        }
        $parent = Split-Path -Parent $cur
        if (-not $parent -or $parent -eq $cur) {
            break
        }
        $cur = $parent
    }
    throw "Raiz do projeto nao encontrada."
}

function Resolve-AbsolutePath([string]$PathText, [string]$BaseDir) {
    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return [System.IO.Path]::GetFullPath($PathText)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathText))
}

function Assert-FileExists([string]$PathText, [string]$Label) {
    if (-not (Test-Path -LiteralPath $PathText -PathType Leaf)) {
        throw "[ERRO] Arquivo nao encontrado em ${Label}: $PathText"
    }
}

function Resolve-ExistingFile([string]$PreferredPath, [string]$BaseDir, [string]$LeafName, [string]$Label) {
    if (Test-Path -LiteralPath $PreferredPath -PathType Leaf) {
        return $PreferredPath
    }
    $fallback = Get-ChildItem -LiteralPath $BaseDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq $LeafName } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($fallback) {
        return $fallback.FullName
    }
    throw "[ERRO] Arquivo nao encontrado em ${Label}: $PreferredPath"
}

function Assert-Dir([string]$PathText) {
    if (-not (Test-Path -LiteralPath $PathText -PathType Container)) {
        New-Item -ItemType Directory -Path $PathText -Force | Out-Null
    }
}

function Get-LatestFileOrThrow([string]$BaseDir, [string]$Pattern, [string]$Label) {
    $file = Get-ChildItem -LiteralPath $BaseDir -File | Where-Object { $_.Name -like $Pattern } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $file) {
        throw "[ERRO] Arquivo nao encontrado em ${Label} com padrao: $Pattern"
    }
    return $file.FullName
}

function Convert-ToAsciiSlug([string]$Text) {
    if ($null -eq $Text) {
        $Text = ""
    }
    $normalized = $Text.Normalize([Text.NormalizationForm]::FormD)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $normalized.ToCharArray()) {
        $cat = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch)
        if ($cat -eq [Globalization.UnicodeCategory]::NonSpacingMark) {
            continue
        }
        [void]$sb.Append($ch)
    }
    $ascii = $sb.ToString().ToLowerInvariant()
    $ascii = [regex]::Replace($ascii, "[^a-z0-9]+", "-")
    $ascii = [regex]::Replace($ascii, "-{2,}", "-").Trim("-")
    if ([string]::IsNullOrWhiteSpace($ascii)) {
        return "sermao"
    }
    return $ascii
}

function Get-CleanWorkspaceStem([string]$Text) {
    if ($null -eq $Text) {
        $Text = ""
    }
    $value = $Text
    $patterns = @(
        "__dossie$",
        "__sermao$",
        "__relatorio_tecnico__gpt-[^_]+",
        "__relatorio_tecnico__.*?(?=__sermao__|$)",
        "__sermao__gpt-[^_]+$",
        "__sermao__.*$"
    )
    foreach ($pattern in $patterns) {
        $value = [regex]::Replace($value, $pattern, "", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    }
    $value = [regex]::Replace($value, "^\d{1,3}__+", "")
    $value = [regex]::Replace($value, "^\d{1,3}_+", "")
    $value = [regex]::Replace($value, "\s+", " ").Trim(" ", "_", "-")
    if ([string]::IsNullOrWhiteSpace($value)) {
        return "documento"
    }
    return $value
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Get-ProjectRoot $ScriptDir
Set-Location $ProjectRoot

$RelatorioScript = Join-Path $ScriptDir "gerar_relatorio_tecnico_de_docx.py"
$RelatorioExportScript = Join-Path $ScriptDir "exportar_formatos_relatorio_md.py"
$SermaoScript = Join-Path $ScriptDir "gerar_sermao_de_relatorio.py"
$ExportScript = Join-Path $ScriptDir "exportar_formatos_sermao_md.py"
$PublishScript = Join-Path $ScriptDir "pipeline_publicar_sermao.py"

$DocxAbs = Resolve-AbsolutePath $Docx $ProjectRoot
Assert-FileExists $DocxAbs "-Docx"
Assert-FileExists $RelatorioScript "script de relatorio"
Assert-FileExists $RelatorioExportScript "script de exportacao do relatorio"
Assert-FileExists $SermaoScript "script de sermao"
Assert-FileExists $ExportScript "script de exportacao"
Assert-FileExists $PublishScript "script de publicacao"

$RelatoriosAbs = Resolve-AbsolutePath $RelatoriosOutDir $ProjectRoot
$DossiesFormatadosAbs = Resolve-AbsolutePath $DossiesFormatadosOutDir $ProjectRoot
$SermoesAbs = Resolve-AbsolutePath $SermoesOutDir $ProjectRoot
$FormatadosAbs = Resolve-AbsolutePath $FormatadosOutDir $ProjectRoot

Assert-Dir $RelatoriosAbs
Assert-Dir $DossiesFormatadosAbs
Assert-Dir $SermoesAbs
Assert-Dir $FormatadosAbs

$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($DocxAbs)
if ([string]::IsNullOrWhiteSpace($Titulo)) {
    $Titulo = $BaseName
}
$BaseSlug = Convert-ToAsciiSlug (Get-CleanWorkspaceStem $BaseName)
$PrefixMatch = [regex]::Match($BaseName, "^(?<prefix>\d{1,3})__")
$Prefix = if ($PrefixMatch.Success) { "{0:D2}__" -f [int]$PrefixMatch.Groups["prefix"].Value } else { "" }
$BaseStem = "$Prefix$BaseSlug"
$RelatorioMdName = "{0}__dossie.md" -f $BaseStem
$SermaoMdName = "{0}__sermao.md" -f $BaseStem
$RelatorioMd = Join-Path $RelatoriosAbs $RelatorioMdName
$SermaoMd = Join-Path $SermoesAbs $SermaoMdName

Write-Host "[1/4] Gerando relatorio tecnico..." -ForegroundColor Cyan
& python $RelatorioScript `
    --docx $DocxAbs `
    --outdir $RelatoriosAbs `
    --model $Model `
    --max-chars $MaxChars
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na geracao do relatorio tecnico." }
$RelatorioMd = Resolve-ExistingFile $RelatorioMd $RelatoriosAbs $RelatorioMdName "relatorio tecnico"

Write-Host "[2/5] Exportando formatos do relatorio tecnico..." -ForegroundColor Cyan
& python $RelatorioExportScript `
    --md $RelatorioMd `
    --outdir $DossiesFormatadosAbs
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na exportacao do relatorio tecnico." }
$RelatorioHtmlA4 = Get-LatestFileOrThrow $DossiesFormatadosAbs "*__dossie__a4.html" "Relatorio HTML A4"
$RelatorioDocxA4 = Get-LatestFileOrThrow $DossiesFormatadosAbs "*__dossie__a4.docx" "Relatorio DOCX A4"
Assert-FileExists $RelatorioHtmlA4 "Relatorio HTML A4"
Assert-FileExists $RelatorioDocxA4 "Relatorio DOCX A4"

Write-Host "[3/5] Gerando sermao a partir do relatorio..." -ForegroundColor Cyan
& python $SermaoScript `
    --relatorio $RelatorioMd `
    --outdir $SermoesAbs `
    --model $Model
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na geracao do sermao." }
$SermaoMd = Resolve-ExistingFile $SermaoMd $SermoesAbs $SermaoMdName "sermao em Markdown"

Write-Host "[4/5] Exportando formatos finais..." -ForegroundColor Cyan
& python $ExportScript `
    --md $SermaoMd `
    --outdir $FormatadosAbs
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na exportacao dos formatos do sermao." }
$HtmlA4 = Get-LatestFileOrThrow $FormatadosAbs "*__sermao__a4.html" "HTML A4"
$HtmlA5 = Get-LatestFileOrThrow $FormatadosAbs "*__sermao__a5.html" "HTML A5"
$HtmlTablet = Get-LatestFileOrThrow $FormatadosAbs "*__sermao__tablet.html" "HTML Tablet"
$DocxA4 = Get-LatestFileOrThrow $FormatadosAbs "*__sermao__a4.docx" "DOCX A4"
Assert-FileExists $HtmlA4 "HTML A4"
Assert-FileExists $HtmlA5 "HTML A5"
Assert-FileExists $HtmlTablet "HTML Tablet"
Assert-FileExists $DocxA4 "DOCX A4"

Write-Host "[5/5] Publicando no app 'sermoes'..." -ForegroundColor Cyan
$PublishArgs = @(
    $PublishScript,
    '--titulo', $Titulo,
    '--serie', $Serie,
    '--resumo', $Resumo,
    '--ordem', $Ordem,
    '--slug', $(if ([string]::IsNullOrWhiteSpace($Slug)) { $BaseSlug } else { $Slug }),
    '--html-a4', $HtmlA4,
    '--html-a5', $HtmlA5,
    '--html-tablet', $HtmlTablet,
    '--docx-a4', $DocxA4,
    '--relatorio-html', $RelatorioHtmlA4
)

if ($Visivel) {
    $PublishArgs += '--visivel'
}

& python @PublishArgs
if ($LASTEXITCODE -ne 0) { throw "[ERRO] Falha na publicacao do sermao no Django." }

Write-Host ""
Write-Host "[OK] Pipeline completo concluido com sucesso." -ForegroundColor Green
Write-Host "     DOCX origem : $DocxAbs"
Write-Host "     Titulo      : $Titulo"
Write-Host "     Serie       : $Serie"
