# C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\tools\zip_projeto_sem_venv.ps1
#========================= UTILIZE ASSIM: =====================================
# Na raiz, digite:
#     cd tools
#     .\zip_projeto_sem_venv.ps1
#==============================================================

param(
    [string]$Projeto = "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado",
    [string]$Saida   = "C:\Users\Wanderley\Apps\Backups"
)

$ErrorActionPreference = "Stop"

function Test-BadLeafName {
    param([string]$Name)

    # termina com ponto ou espaço
    if ($Name -match '[\.\s]$') { return $true }

    # caracteres da área privada Unicode (muito comuns em nomes “quebrados”)
    foreach ($ch in $Name.ToCharArray()) {
        $code = [int][char]$ch
        if ($code -ge 0xE000 -and $code -le 0xF8FF) {
            return $true
        }
    }

    return $false
}

if (!(Test-Path -LiteralPath $Projeto)) {
    throw "Pasta do projeto não encontrada: $Projeto"
}

if (!(Test-Path -LiteralPath $Saida)) {
    New-Item -ItemType Directory -Path $Saida | Out-Null
}

$nomeProjeto = Split-Path $Projeto -Leaf
$data        = Get-Date -Format "yyyyMMdd_HHmmss"
$temp        = Join-Path $env:TEMP "${nomeProjeto}_zip_temp_$data"
$zipFinal    = Join-Path $Saida "${nomeProjeto}_sem_venv_$data.zip"
$logPulados  = Join-Path $Saida "${nomeProjeto}_itens_pulados_$data.txt"

Write-Host "Projeto : $Projeto"
Write-Host "Saída   : $zipFinal"
Write-Host "Temp    : $temp"
Write-Host ""

if (Test-Path -LiteralPath $temp) {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
New-Item -ItemType Directory -Path $temp | Out-Null

# Copia tudo, exceto pastas/arquivos técnicos desnecessários
robocopy $Projeto $temp /E /XD `
    "$Projeto\venv" `
    "$Projeto\.git" `
    "$Projeto\__pycache__" `
    "$Projeto\.mypy_cache" `
    "$Projeto\.pytest_cache" `
    /XF `
    "*.pyc" `
    "*.pyo" `
    "*.log"

if ($LASTEXITCODE -gt 7) {
    throw "Erro no robocopy. Código: $LASTEXITCODE"
}

# Identifica itens problemáticos na cópia temporária
$badItems = Get-ChildItem -LiteralPath $temp -Recurse -Force |
    Where-Object { Test-BadLeafName $_.Name }

if ($badItems) {
    Write-Host "Foram encontrados itens com nome problemático. Eles serão removidos apenas da cópia temporária."
    $badItems |
        Sort-Object FullName |
        Select-Object -ExpandProperty FullName |
        Set-Content -LiteralPath $logPulados -Encoding UTF8

    $badItems |
        Sort-Object FullName -Descending |
        ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force
        }

    Write-Host "Lista gravada em: $logPulados"
    Write-Host ""
}

if (Test-Path -LiteralPath $zipFinal) {
    Remove-Item -LiteralPath $zipFinal -Force
}

# Compactação mais robusta
$tarCmd = Get-Command tar.exe -ErrorAction SilentlyContinue
if ($tarCmd) {
    & tar.exe -a -c -f $zipFinal -C $temp .
}
else {
    $topItems = Get-ChildItem -LiteralPath $temp -Force | Select-Object -ExpandProperty FullName
    Compress-Archive -LiteralPath $topItems -DestinationPath $zipFinal -Force
}

if (!(Test-Path -LiteralPath $zipFinal)) {
    throw "O ZIP não foi criado."
}

# Limpa temporário
Remove-Item -LiteralPath $temp -Recurse -Force

Write-Host ""
Write-Host "ZIP criado com sucesso:"
Write-Host $zipFinal