param(
  [string]$Root = "",
  [string]$InputDir = "",
  [string]$InputDirArtigos = "",
  [string]$WorkspaceArtigos = "",
  [switch]$ScanOnly,
  [switch]$Browse,
  [switch]$OpenBrowse,
  [switch]$DryRun,
  [switch]$Execute,
  [int]$Limit = 0,
  [string]$Serie = "",
  [string]$Autor = "",
  [string]$Pasta = "",
  [string]$Search = "",
  [string]$StatusManifest = "",
  [string]$StatusExecucao = "",
  [switch]$OnlyPublished,
  [switch]$OnlyUnpublished,
  [switch]$OnlyChanged,
  [switch]$RetryFailed,
  [switch]$ContinueOnError,
  [switch]$SkipIfExists,
  [string]$SelectionFile = "",
  [string]$RunnerTemplate = "",
  [string]$UnitScript = "",
  [string]$ResumoPadrao = "",
  [string]$DjangoSettings = "",
  [switch]$NoDbHydrate,
  [switch]$NoArticlesContext
)

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

if (-not $InputDir) {
  throw "Informe -InputDir com a pasta-base dos sermões formatados."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = if ($Root) { [System.IO.Path]::GetFullPath($Root) } else { Get-ProjectRoot $scriptDir }
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
$py = Join-Path $scriptDir "orquestrador_sermoes.py"
$args = @("$py", "--root", $projectRoot, "--input-dir", $InputDir)

if ($InputDirArtigos) { $args += @("--input-dir-artigos", $InputDirArtigos) }
if ($WorkspaceArtigos) { $args += @("--workspace-artigos", $WorkspaceArtigos) }
if ($ScanOnly) { $args += "--scan-only" }
if ($Browse) { $args += "--browse" }
if ($OpenBrowse) { $args += "--open-browse" }
if ($DryRun) { $args += "--dry-run" }
if ($Execute) { $args += "--execute" }
if ($Limit -gt 0) { $args += @("--limit", "$Limit") }
if ($Serie) { $args += @("--serie", $Serie) }
if ($Autor) { $args += @("--autor", $Autor) }
if ($Pasta) { $args += @("--pasta", $Pasta) }
if ($Search) { $args += @("--search", $Search) }
if ($StatusManifest) { $args += @("--status-manifest", $StatusManifest) }
if ($StatusExecucao) { $args += @("--status-execucao", $StatusExecucao) }
if ($OnlyPublished) { $args += "--only-published" }
if ($OnlyUnpublished) { $args += "--only-unpublished" }
if ($OnlyChanged) { $args += "--only-changed" }
if ($RetryFailed) { $args += "--retry-failed" }
if ($ContinueOnError) { $args += "--continue-on-error" }
if ($SkipIfExists) { $args += "--skip-if-exists" }
if ($SelectionFile) { $args += @("--selection-file", $SelectionFile) }
if ($RunnerTemplate) { $args += @("--runner-template", $RunnerTemplate) }
if ($UnitScript) { $args += @("--unit-script", $UnitScript) }
if ($ResumoPadrao) { $args += @("--resumo-padrao", $ResumoPadrao) }
if ($DjangoSettings) { $args += @("--django-settings", $DjangoSettings) }
if ($NoDbHydrate) { $args += "--no-db-hydrate" }
if ($NoArticlesContext) { $args += "--no-articles-context" }

& $pythonExe @args
