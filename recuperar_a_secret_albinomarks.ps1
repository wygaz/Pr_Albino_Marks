# 0) (opcional) limpa variáveis antigas
if (Test-Path variable:res) { Remove-Variable res -ErrorAction SilentlyContinue }
if (Test-Path variable:secretJson) { Remove-Variable secretJson -ErrorAction SilentlyContinue }
if (Test-Path variable:creds) { Remove-Variable creds -ErrorAction SilentlyContinue }

# 1) Buscar secret e obter SecretString cru
$res = aws secretsmanager get-secret-value --secret-id albinomarks-media/s3 --profile aws-adm --region us-east-1 --output json | ConvertFrom-Json
$secretRaw = $res.SecretString

# 2) diagnóstico rápido - mostrar primeiro 120 caracteres "visíveis" (substitui control-chars por pontos)
$preview = $secretRaw.Substring(0, [math]::Min(120, $secretRaw.Length))
$previewVisible = ($preview.ToCharArray() | ForEach-Object { if ([char]::IsControl($_)) { '.' } else { $_ } }) -join ''
Write-Host "`n--- PREVIEW (primeiros chars) ---"
Write-Host $previewVisible

# 3) mostrar os primeiros bytes em hex (verifica BOM: EF BB BF)
$bytes = [System.Text.Encoding]::UTF8.GetBytes($secretRaw)
$hexHead = ($bytes[0..([math]::Min(9,$bytes.Length-1))] | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
Write-Host "`n--- BYTES (início, hex) ---"
Write-Host $hexHead

# 4) Remover BOM unicode (U+FEFF) e também caracteres invisíveis Unicode comuns (zero-width)
$secretClean = $secretRaw.TrimStart([char]0xFEFF, [char]0x200B, [char]0x00A0).Trim()

# 5) Se ainda houver lixo antes do primeiro '{', extrair do primeiro '{' até o último '}'
$first = $secretClean.IndexOf('{')
$last = $secretClean.LastIndexOf('}')
if ($first -ge 0 -and $last -ge $first) {
    $jsonOnly = $secretClean.Substring($first, $last - $first + 1)
} else {
    $jsonOnly = $secretClean
}

# 6) diagnóstico do trecho que será parseado
Write-Host "`n--- TRECHO QUE VOU PARSEAR (primeiros 230 chars) ---"
Write-Host ($jsonOnly.Substring(0,[math]::Min(230,$jsonOnly.Length)))

# 7) Agora converte para objeto PowerShell, com try/catch para mostrar erro legível
try {
    $creds = $jsonOnly | ConvertFrom-Json -ErrorAction Stop
    Write-Host "`n=== CONVERTIDO COM SUCESSO ==="
    # mostrar as chaves (sem valores sensíveis)
    $creds | Get-Member -MemberType NoteProperty | ForEach-Object { $_.Name }
} catch {
    Write-Host "`n*** ERRO AO PARSEAR JSON: ***"
    Write-Host $_.Exception.Message
    Write-Host "`nSe aparecer 'JSON primitivo inválido', cole aqui a saída dos blocos 'PREVIEW' e 'BYTES' acima."
}
