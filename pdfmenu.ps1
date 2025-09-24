# pdfmenu.ps1 — menu para gerar PDFs a partir de DOCX sem digitar slug
# Requer: Python/venv ok, manage.py acessível, LIBREOFFICE_PATH configurado no .env

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# Sempre usar o python do venv se existir
$python = Join-Path $here "venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

# Busca artigos (slug, título) e se têm DOCX, via Django
$py = @'
from A_Lei_no_NT.models import Artigo
import json
def has_docx(a):
    try:
        return bool(a.arquivo_word and a.arquivo_word.name)
    except Exception:
        return False
arts = Artigo.objects.filter(visivel=True).order_by("ordem","titulo")
data = [{"slug": a.slug, "titulo": a.titulo, "has_docx": has_docx(a)} for a in arts]
print(json.dumps(data, ensure_ascii=False))
'@

$json = & $python manage.py shell -c $py
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($json)) {
  Write-Host "Falha ao consultar artigos via Django." -ForegroundColor Red
  exit 1
}

$list = $json | ConvertFrom-Json | Where-Object { $_.has_docx -eq $true }
if (-not $list) {
  Write-Host "Não há artigos com DOCX disponível." -ForegroundColor Yellow
  exit
}

# Menu com filtro
function Show($items) {
  $i=1
  foreach ($a in $items) {
    "{0,2}. {1}  (slug: {2})" -f $i, $a.titulo, $a.slug
    $i++
  }
}

$view = $list
while ($true) {
  Clear-Host
  Write-Host "====== Gerar PDF a partir de DOCX ======" -ForegroundColor Cyan
  Write-Host "Dica: digite texto para filtrar; 'tudo' para selecionar todos; ENTER para sair.`n"
  Show $view
  Write-Host ""
  $inp = Read-Host "Informe número(s) (ex: 1,3,5) / termo de busca / 'tudo'"

  if ([string]::IsNullOrWhiteSpace($inp)) { break }

  if ($inp -match '^(?i)tudo$') {
    $targets = $view
  }
  elseif ($inp -match '^\d') {
    $nums = $inp -split '[,; ]+' | Where-Object { $_ -match '^\d+$' } | ForEach-Object {[int]$_}
    $targets = @()
    foreach ($n in $nums) {
      if ($n -ge 1 -and $n -le $view.Count) { $targets += $view[$n-1] }
    }
    if (-not $targets) { Write-Host "Sem seleção válida." -ForegroundColor Yellow; Start-Sleep -Seconds 1; continue }
  }
  else {
    $view = $list | Where-Object { $_.titulo -match [regex]::Escape($inp) -or $_.slug -match [regex]::Escape($inp) }
    if (-not $view) { Write-Host "Nada encontrado para '$inp'." -ForegroundColor Yellow; $view = $list; Start-Sleep -Seconds 1 }
    continue
  }

  # Executa geração para cada slug selecionado
  foreach ($t in $targets) {
    Write-Host "`nGerando PDF: $($t.titulo)  (slug: $($t.slug))" -ForegroundColor Green
    & $python manage.py gerar_pdfs_local --slug $t.slug
    if ($LASTEXITCODE -ne 0) { Write-Host "Falha ao gerar $($t.slug)." -ForegroundColor Red }
  }
  Read-Host "`nConcluído. ENTER para voltar ao menu (ou feche a janela)"
}
