# requires -version 5
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# Liste .bat (exceto este lançador, se for .bat)
$items = Get-ChildItem -LiteralPath $here -Filter *.bat |
         Where-Object { $_.Name -ne 'run.bat' } |
         Sort-Object Name

if (-not $items) {
  Write-Host "Não há .bat nesta pasta." -ForegroundColor Yellow
  exit
}

function Show-Menu($list) {
  $i = 1
  foreach ($f in $list) {
    "{0,2}. {1}" -f $i, $f.Name
    $i++
  }
}

Write-Host ""
Write-Host "====== Selecione um .BAT, pelo seu número de ordem, para executar ======"

$view = $items
while ($true) {
  Write-Host ""
  Show-Menu $view
  Write-Host ""
  $inp = Read-Host "Digite número, ou texto para filtrar, ENTER para sair"

  if ([string]::IsNullOrWhiteSpace($inp)) { break }

  if ($inp -as [int]) {
    $n = [int]$inp
    if ($n -ge 1 -and $n -le $view.Count) {
      $file = $view[$n-1].FullName
      Write-Host ""
      Write-Host "Executando: $($view[$n-1].Name)"
      Write-Host "--------------------------------"
      & cmd.exe /c "`"$file`""
      break
    } else {
      Write-Host "Número fora do intervalo." -ForegroundColor Yellow
    }
  } else {
    $view = $items | Where-Object { $_.Name -match [regex]::Escape($inp) }
    if (-not $view) {
      Write-Host "Nenhum .bat corresponde a '$inp'." -ForegroundColor Yellow
      $view = $items
    }
  }
}
