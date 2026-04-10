param(
    [string]$Bucket = "albinomarks-media",
    [string]$Lista = "refs_uploads_artigos_unicos.txt",
    [string]$Destino = ".\downloads_referenciados",
    [switch]$NoVerifySSL
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Lista)) {
    throw "Arquivo de lista não encontrado: $Lista"
}

New-Item -ItemType Directory -Force -Path $Destino | Out-Null

function Get-FallbackKey([string]$path) {
    return ($path -replace '_[A-Za-z0-9]{7}\.docx$', '.docx')
}

$linhas = Get-Content $Lista -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object {
        $_ -ne "" `
        -and $_ -like "uploads/artigos/*" `
        -and $_ -notlike "uploads/artigos/2025-11-25_*" `
        -and $_ -notlike "uploads/artigos/1_ORIGEM_DO_GRANDE_CONFLITO_*"
    }

$ok = 0
$fallbackOk = 0
$falhou = 0
$logFalhas = @()

foreach ($path in $linhas) {
    $nomeArquivo = Split-Path $path -Leaf
    $destinoFinal = Join-Path $Destino $nomeArquivo

    if (Test-Path $destinoFinal) {
        Write-Host "Já existe, pulando: $nomeArquivo"
        continue
    }

    $s3uri = "s3://$Bucket/$path"
    Write-Host "Tentando exato: $nomeArquivo"

    if ($NoVerifySSL) {
        aws s3 cp $s3uri $destinoFinal --no-verify-ssl | Out-Null
    } else {
        aws s3 cp $s3uri $destinoFinal | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        $ok++
        continue
    }

    $fallback = Get-FallbackKey $path

    if ($fallback -ne $path) {
        $fallbackUri = "s3://$Bucket/$fallback"
        Write-Host "  Tentando fallback: $(Split-Path $fallback -Leaf)"

        if ($NoVerifySSL) {
            aws s3 cp $fallbackUri $destinoFinal --no-verify-ssl | Out-Null
        } else {
            aws s3 cp $fallbackUri $destinoFinal | Out-Null
        }

        if ($LASTEXITCODE -eq 0) {
            $ok++
            $fallbackOk++
            continue
        }
    }

    $falhou++
    $logFalhas += $path
    Write-Warning "Falhou: $nomeArquivo"
}

$logFalhas | Set-Content -Encoding UTF8 .\faltas_reais_s3.txt

Write-Host ""
Write-Host "Baixados com sucesso: $ok"
Write-Host "Recuperados por fallback: $fallbackOk"
Write-Host "Falhas: $falhou"
Write-Host "Lista de falhas reais: .\faltas_reais_s3.txt"