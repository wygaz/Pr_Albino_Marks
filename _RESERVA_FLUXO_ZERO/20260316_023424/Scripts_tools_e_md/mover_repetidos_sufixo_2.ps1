param(
    [Parameter(Mandatory=$true)]
    [string]$Origem,

    [Parameter(Mandatory=$true)]
    [string]$DestinoRepetidos,

    [string]$Sufixo = "_2",

    [switch]$Simular
)

function Get-NomeBaseSemSufixo {
    param(
        [string]$NomeArquivo,
        [string]$SufixoAlvo
    )

    $base = [System.IO.Path]::GetFileNameWithoutExtension($NomeArquivo)
    $ext  = [System.IO.Path]::GetExtension($NomeArquivo)

    if ($base -match [regex]::Escape($SufixoAlvo) + '$') {
        $baseLimpo = $base -replace ([regex]::Escape($SufixoAlvo) + '$'), ''
        return "$baseLimpo$ext"
    }

    return $NomeArquivo
}

if (-not (Test-Path $Origem)) {
    throw "Diretório de origem não encontrado: $Origem"
}

New-Item -ItemType Directory -Force -Path $DestinoRepetidos | Out-Null

$arquivos = Get-ChildItem -Path $Origem -File

# Índice por nome exato
$porNome = @{}
foreach ($a in $arquivos) {
    $porNome[$a.Name] = $a
}

$paresEncontrados = 0

foreach ($arquivo in $arquivos) {
    $nomeOriginalEsperado = Get-NomeBaseSemSufixo -NomeArquivo $arquivo.Name -SufixoAlvo $Sufixo

    # Só interessa se este arquivo termina com o sufixo, ex: arquivo_2.docx
    if ($nomeOriginalEsperado -ne $arquivo.Name -and $porNome.ContainsKey($nomeOriginalEsperado)) {
        $paresEncontrados++

        $original  = $porNome[$nomeOriginalEsperado]
        $duplicado = $arquivo

        $ordenados = @($original, $duplicado) | Sort-Object LastWriteTime -Descending
        $manter = $ordenados[0]
        $mover  = $ordenados[1]

        Write-Host ""
        Write-Host "Par encontrado:" -ForegroundColor Cyan
        Write-Host "  ORIGINAL : $($original.Name)  | $($original.LastWriteTime)"
        Write-Host "  DUPLICADO: $($duplicado.Name) | $($duplicado.LastWriteTime)"
        Write-Host "  MANTER   : $($manter.Name)" -ForegroundColor Green
        Write-Host "  MOVER    : $($mover.Name)" -ForegroundColor Yellow

        $destinoFinal = Join-Path $DestinoRepetidos $mover.Name

        if (Test-Path $destinoFinal) {
            $base = [System.IO.Path]::GetFileNameWithoutExtension($mover.Name)
            $ext  = [System.IO.Path]::GetExtension($mover.Name)
            $stamp = $mover.LastWriteTime.ToString("yyyyMMdd_HHmmss")
            $destinoFinal = Join-Path $DestinoRepetidos "${base}__old_${stamp}${ext}"
        }

        if (-not $Simular) {
            Move-Item -Path $mover.FullName -Destination $destinoFinal
        }
    }
}

Write-Host ""
Write-Host "Pares encontrados: $paresEncontrados" -ForegroundColor Magenta

if ($Simular) {
    Write-Host "Simulação concluída. Nenhum arquivo foi movido." -ForegroundColor Yellow
} else {
    Write-Host "Processamento concluído." -ForegroundColor Green
}