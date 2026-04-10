param(
    [string]$Projeto = "C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado",
    [string]$SaidaZip = "C:\Users\Wanderley\Apps\Backups\Pr_Albino_Marks_restaurado_repo.zip"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $Projeto)) {
    throw "Projeto não encontrado: $Projeto"
}

Set-Location $Projeto

# Verifica se é repositório git
git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "A pasta não parece ser um repositório Git válido."
}

# Procura arquivos sensíveis já rastreados
$matches = git ls-files | Select-String -Pattern '(^Apenas_Local/|^media/|\.env($|\.)|\.key$|\.pem$|\.pfx$|\.crt$|\.cer$|db\.sqlite3$|\.sqlite3$)'

if ($matches) {
    Write-Host ""
    Write-Host "ATENÇÃO: encontrei arquivos sensíveis já rastreados pelo Git."
    Write-Host "Revise antes de gerar o ZIP:"
    $matches | ForEach-Object { $_.Line }
    Write-Host ""
    throw "Abortado por segurança."
}

$dirSaida = Split-Path $SaidaZip -Parent
if (!(Test-Path -LiteralPath $dirSaida)) {
    New-Item -ItemType Directory -Path $dirSaida | Out-Null
}

if (Test-Path -LiteralPath $SaidaZip) {
    Remove-Item -LiteralPath $SaidaZip -Force
}

git archive --format=zip --output="$SaidaZip" HEAD
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar ZIP com git archive."
}

Write-Host ""
Write-Host "ZIP sanitizado criado com sucesso:"
Write-Host $SaidaZip