# push_secret_albinomarks.ps1
# Uso: roda no PowerShell com AWS CLI configurado com permissões admin (profile aws-adm)
# NÃO compartilhe as chaves que inserir aqui.
#Este Script está preparado para enviar 

$profile = "aws-adm"
$region = "us-east-1"
$secretName = "albinomarks-media/s3"
$tempFile = Join-Path (Get-Location) "secret_s3.json"

Write-Host "Vamos criar/atualizar o Secret: $secretName (região $region)."

# 1) Ler AccessKeyId e SecretAccessKey do usuário (secret lido como SecureString)
$accessId = Read-Host "Cole aqui o AWS Access Key ID (formato AKIA...)" 
$secure = Read-Host "Cole aqui o AWS Secret Access Key (será lido de forma segura)" -AsSecureString
# converter SecureString para plain text temporário (apenas em memória)
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$secretKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)  # limpa o ponteiro

# 2) Montar o JSON do secret (em memória) e gravar em arquivo temporário seguro
$secretObj = @{
    AWS_ACCESS_KEY_ID = $accessId
    AWS_SECRET_ACCESS_KEY = $secretKey
    AWS_STORAGE_BUCKET_NAME = "albinomarks-media"
    AWS_S3_REGION_NAME = "us-east-1"
}
$secretJson = $secretObj | ConvertTo-Json -Depth 4

# escreve arquivo temporário com permissões padrão
$secretJson | Set-Content -Path $tempFile -Encoding UTF8
Write-Host "Arquivo temporário criado em $tempFile (será removido em breve)."

# 3) Verificar se o secret já existe; se existir, atualiza; se não, cria
try {
    $exists = aws secretsmanager describe-secret --secret-id $secretName --profile $profile --region $region --output text 2>$null
    $existsFlag = $true
} catch {
    $existsFlag = $false
}

if ($existsFlag) {
    Write-Host "Secret já existe — atualizando com nova versão..."
    aws secretsmanager put-secret-value --secret-id $secretName --secret-string file://$tempFile --profile $profile --region $region
    Write-Host "Secret atualizado: $secretName" -ForegroundColor Green
} else {
    Write-Host "Secret não existe — criando novo secret..."
    aws secretsmanager create-secret --name $secretName --description "S3 creds for Albinomarks" --secret-string file://$tempFile --profile $profile --region $region
    Write-Host "Secret criado: $secretName" -ForegroundColor Green
}

# 4) Limpeza do arquivo temporário
try {
    Remove-Item $tempFile -Force
    Write-Host "Arquivo temporário removido."
} catch {
    Write-Host "Falha ao remover arquivo temporário. Remova manualmente: $tempFile" -ForegroundColor Yellow
}

# 5) Limpar variável que continha o secret em plain text
$secretKey = $null
$secure = $null

# 6) Teste (opcional): recuperar o secret e testar listagem do bucket usando as credenciais nele salvadas
Write-Host ""
Write-Host "Agora vamos recuperar o Secret e testar listagem do bucket (apenas na sessão atual)."
$secretJsonFromAws = aws secretsmanager get-secret-value --secret-id $secretName --profile $profile --region $region --query SecretString --output text
if (-not $secretJsonFromAws) {
    Write-Host "Não foi possível recuperar o secret para teste. Verifique permissões/nomes." -ForegroundColor Red
    exit 1
}
$creds = ConvertFrom-Json $secretJsonFromAws

# Exportar apenas para a sessão atual (teste)
$env:AWS_ACCESS_KEY_ID = $creds.AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY = $creds.AWS_SECRET_ACCESS_KEY
$env:AWS_DEFAULT_REGION = $creds.AWS_S3_REGION_NAME

Write-Host "Credenciais carregadas temporariamente na sessão. Testando: aws s3 ls s3://$($creds.AWS_STORAGE_BUCKET_NAME) --region $env:AWS_DEFAULT_REGION"
try {
    aws s3 ls s3://$($creds.AWS_STORAGE_BUCKET_NAME) --region $env:AWS_DEFAULT_REGION
    Write-Host "Teste de listagem concluído (se não houve erro, as credenciais estão corretas)." -ForegroundColor Green
} catch {
    Write-Host "Erro no teste de S3. Mensagem:" -ForegroundColor Red
    Write-Host $_
}

Write-Host ""
Write-Host "IMPORTANTE: As variáveis AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY estão apenas na sessão atual. Para removê-las, rode:"
Write-Host "Remove-Item env:AWS_ACCESS_KEY_ID; Remove-Item env:AWS_SECRET_ACCESS_KEY; Remove-Item env:AWS_DEFAULT_REGION" -ForegroundColor Yellow

Write-Host ""
Write-Host "Se quiser, posso (a) anexar uma policy de leitura desse Secret ao usuário wyg-aws, (b) agendar exclusão do Secret antigo, ou (c) gerar instruções para atualizar as variáveis no Railway. O que prefere fazer em seguida?"
