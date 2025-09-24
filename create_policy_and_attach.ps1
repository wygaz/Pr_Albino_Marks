# ===========================
# create_policy_and_attach.ps1
# ===========================
# Ajuste estas variáveis se necessário
$secretId = "albinomarks/s3"
$region = "us-east-1"
$userName = "wyg-aws"
$policyName = "AlbinomarksSecretsReadOnly"
$policyFile = ".\policy_secrets_access.json"

Write-Host "1) Obtendo ARN do secret '$secretId' (region: $region) ..."
try {
    $secretArn = aws secretsmanager describe-secret --secret-id $secretId --region $region --query 'ARN' --output text
} catch {
    Write-Host "ERRO: não foi possível encontrar o secret '$secretId'. Se ele ainda não existe, crie-o primeiro com 'aws secretsmanager create-secret ...'." -ForegroundColor Red
    throw
}

if (-not $secretArn) {
    Write-Host "ERRO: ARN vazio. Verifique o secretId e suas permissões." -ForegroundColor Red
    exit 1
}

Write-Host "Secret ARN encontrado: $secretArn" -ForegroundColor Green

Write-Host "2) Gerando arquivo de policy JSON em $policyFile ..."
# Monta o JSON dinamicamente com o ARN retornado
$policyObj = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Sid = "AllowReadSpecificSecret"
            Effect = "Allow"
            Action = @("secretsmanager:GetSecretValue","secretsmanager:DescribeSecret")
            Resource = $secretArn
        }
    )
}
# ConvertTo-Json precisa de profundidade suficiente
$policyJson = $policyObj | ConvertTo-Json -Depth 6
Set-Content -Path $policyFile -Value $policyJson -Encoding UTF8
Write-Host "Policy JSON salvo em $policyFile" -ForegroundColor Green

Write-Host "3) Criando a policy IAM '$policyName' ..."
try {
    $policyArn = aws iam create-policy --policy-name $policyName --policy-document file://$policyFile --query 'Policy.Arn' --output text
    Write-Host "Policy criada. ARN: $policyArn" -ForegroundColor Green
} catch {
    # Se a policy já existir, pegar o ARN existente
    Write-Host "A criação da policy falhou (pode já existir). Tentando recuperar ARN de policy existente ..." -ForegroundColor Yellow
    $policyArn = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$policyName'].Arn | [0]" --output text
    if (-not $policyArn) {
        Write-Host "Não foi possível criar ou localizar a policy. Saindo." -ForegroundColor Red
        throw
    } else {
        Write-Host "ARN da policy existente: $policyArn" -ForegroundColor Green
    }
}

Write-Host "4) Anexando a policy ao usuário '$userName' ..."
try {
    aws iam attach-user-policy --user-name $userName --policy-arn $policyArn
    Write-Host "Policy anexada com sucesso a $userName." -ForegroundColor Green
} catch {
    Write-Host "Falha ao anexar policy. Verifique permissões e se o usuário existe." -ForegroundColor Red
    throw
}

Write-Host ""
Write-Host "=== FEITO ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para recuperar o secret e carregar as variáveis na sessão, rode o trecho abaixo (ou execute o script get_secret_and_export.ps1):"
Write-Host ""
Write-Host @'
# -------- recuperar e exportar (cole/execute no PowerShell) --------
$secretId = "albinomarks/s3"
$region = "us-east-1"

# Recupera a string do secret (JSON)
$secretJson = aws secretsmanager get-secret-value --secret-id $secretId --query SecretString --output text --region $region

# Converte para objeto PowerShell
$creds = ConvertFrom-Json $secretJson

# Exporta só para a sessão atual (temporal)
$env:AWS_ACCESS_KEY_ID = $creds.AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY = $creds.AWS_SECRET_ACCESS_KEY
$env:AWS_STORAGE_BUCKET_NAME = $creds.AWS_STORAGE_BUCKET_NAME
$env:AWS_S3_REGION_NAME = $creds.AWS_S3_REGION_NAME

Write-Host "Credenciais carregadas na sessão (temporárias). Teste com: aws s3 ls s3://$($env:AWS_STORAGE_BUCKET_NAME) --region $env:AWS_S3_REGION_NAME"

# Quando terminar, limpe:
# Remove-Item env:AWS_ACCESS_KEY_ID; Remove-Item env:AWS_SECRET_ACCESS_KEY; Remove-Item env:AWS_STORAGE_BUCKET_NAME; Remove-Item env:AWS_S3_REGION_NAME
'@
