param()

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

$Root = Get-ProjectRoot $PSScriptRoot

$Python = $null
try {
    $Python = (Get-Command python -ErrorAction Stop).Source
} catch {
    try {
        $Python = (Get-Command py -ErrorAction Stop).Source
    } catch {
        $Python = Join-Path $Root "venv\Scripts\python.exe"
    }
}
$ScriptBase = Split-Path -Parent $MyInvocation.MyCommand.Path
$Helper = Join-Path $ScriptBase "browse_refresh_helper.py"
$Orquestrador = Join-Path $ScriptBase "orquestrador_sermoes.py"
$InputDirSermoes = Join-Path $Root "Apenas_Local\operacional\sermoes\formatados"
$InputDirArtigos = Join-Path $Root "Apenas_Local\operacional\artigos\series"
$HelperPort = $null

function Get-FreeHelperPort {
    for ($port = 8766; $port -le 8785; $port++) {
        $busy = netstat -ano | Select-String "127\.0\.0\.1:$port\s+.*LISTENING"
        if (-not $busy) {
            return $port
        }
    }
    throw "Nenhuma porta livre encontrada para o helper do Browse."
}

function Test-Helper {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$HelperPort/health" -UseBasicParsing -TimeoutSec 2
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Restart-Helper {
    $script:HelperPort = Get-FreeHelperPort
    Start-Process -FilePath $Python -ArgumentList @($Helper, "--port", "$HelperPort") -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
    Start-Sleep -Milliseconds 800
}

Restart-Helper
if (-not (Test-Helper)) {
    throw "Falha ao iniciar o helper do Browse."
}

& $Python $Orquestrador --input-dir $InputDirSermoes --input-dir-artigos $InputDirArtigos --workspace-artigos $InputDirArtigos --browse --scan-only
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao regenerar o Browse."
}

$BrowseUrl = "http://127.0.0.1:$HelperPort/browse"
Start-Process $BrowseUrl
