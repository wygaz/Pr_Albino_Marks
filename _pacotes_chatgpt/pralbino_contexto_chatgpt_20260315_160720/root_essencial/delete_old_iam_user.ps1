# delete_old_iam_user.ps1
# Uso: rode no PowerShell onde aws cli esteja configurado
# ATENCAO: operações destrutivas. Execute apenas se tiver certeza.

$OldUser = "albinomarks-railway"
$Region = "us-east-1"    # só usado para Secrets Manager cleanup, ajuste se precisar

Write-Host "=== Iniciando remoção do usuário IAM: $OldUser ===" -ForegroundColor Cyan

# 0) Verifica se o usuário existe
try {
    $u = aws iam get-user --user-name $OldUser --output json 2>&1
} catch {
    Write-Host "Usuário '$OldUser' não encontrado ou sem permissões para consultar. Saindo." -ForegroundColor Yellow
    Write-Host $_
    exit 0
}
Write-Host "Usuário encontrado. Prosseguindo..." -ForegroundColor Green

# 1) Listar e deletar access keys (inativar antes)
$ak = aws iam list-access-keys --user-name $OldUser --query 'AccessKeyMetadata[].AccessKeyId' --output text
if ($ak) {
    $keys = $ak -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($k in $keys) {
        Write-Host "Inativando e deletando AccessKey: $k"
        aws iam update-access-key --user-name $OldUser --access-key-id $k --status Inactive
        aws iam delete-access-key --user-name $OldUser --access-key-id $k
    }
} else {
    Write-Host "Nenhuma access key encontrada para $OldUser"
}

# 2) Deletar service-specific credentials (e.g., for CodeCommit)
$svcCreds = aws iam list-service-specific-credentials --user-name $OldUser --query 'ServiceSpecificCredentials[].ServiceSpecificCredentialId' --output text
if ($svcCreds) {
    $svcArr = $svcCreds -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($s in $svcArr) {
        Write-Host "Deleting service-specific credential: $s"
        aws iam delete-service-specific-credential --user-name $OldUser --service-specific-credential-id $s
    }
}

# 3) Deletar SSH public keys (if any)
$sshKeys = aws iam list-ssh-public-keys --user-name $OldUser --query 'SSHPublicKeys[].SSHPublicKeyId' --output text
if ($sshKeys) {
    $sshArr = $sshKeys -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($sid in $sshArr) {
        Write-Host "Removendo SSH public key: $sid"
        aws iam delete-ssh-public-key --user-name $OldUser --ssh-public-key-id $sid
    }
}

# 4) Deletar signing certificates (se houver)
$certs = aws iam list-signing-certificates --user-name $OldUser --query 'Certificates[].CertificateId' --output text
if ($certs) {
    $certArr = $certs -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($c in $certArr) {
        Write-Host "Removendo signing certificate: $c"
        aws iam delete-signing-certificate --user-name $OldUser --certificate-id $c
    }
}

# 5) Remover o usuário de todos os grupos
$groups = aws iam list-groups-for-user --user-name $OldUser --query 'Groups[].GroupName' --output text
if ($groups) {
    $groupsArr = $groups -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($g in $groupsArr) {
        Write-Host "Removendo usuário do grupo: $g"
        aws iam remove-user-from-group --user-name $OldUser --group-name $g
    }
}

# 6) Detach managed policies
$attached = aws iam list-attached-user-policies --user-name $OldUser --query 'AttachedPolicies[].PolicyArn' --output text
if ($attached) {
    $attachedArr = $attached -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($p in $attachedArr) {
        Write-Host "Desanexando policy gerenciada: $p"
        aws iam detach-user-policy --user-name $OldUser --policy-arn $p
    }
}

# 7) Deletar inline policies
$inline = aws iam list-user-policies --user-name $OldUser --query 'PolicyNames' --output text
if ($inline) {
    $inlineArr = $inline -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($pol in $inlineArr) {
        Write-Host "Deletando inline policy: $pol"
        aws iam delete-user-policy --user-name $OldUser --policy-name $pol
    }
}

# 8) Deactivate and delete MFA devices (virtual/hardware)
$mfas = aws iam list-mfa-devices --user-name $OldUser --query 'MFADevices[].SerialNumber' --output text
if ($mfas) {
    $mfasArr = $mfas -split "`t| `n| " | Where-Object { $_ -ne "" }
    foreach ($s in $mfasArr) {
        Write-Host "Deactivating MFA device: $s"
        try { aws iam deactivate-mfa-device --user-name $OldUser --serial-number $s } catch {}
        try { aws iam delete-virtual-mfa-device --serial-number $s } catch {}
    }
}

# 9) Delete login profile (console password)
try {
    aws iam delete-login-profile --user-name $OldUser
    Write-Host "Login profile deletado (se existia)."
} catch {
    Write-Host "Nenhum login-profile ou erro ao deletar. OK."
}

# 10) Remove user tags (optional)
try {
    $tags = aws iam list-user-tags --user-name $OldUser --query 'Tags[].Key' --output text
    if ($tags) {
        $tagArr = $tags -split "`t| `n| " | Where-Object { $_ -ne "" }
        aws iam untag-user --user-name $OldUser --tag-keys $tagArr
        Write-Host "Tags removidas: $tagArr"
    }
} catch {}

# 11) Finally delete the user
Write-Host "Tentando deletar o usuário $OldUser ..."
try {
    aws iam delete-user --user-name $OldUser
    Write-Host "Usuário $OldUser deletado com sucesso." -ForegroundColor Green
} catch {
    Write-Host "Erro ao deletar usuário. Talvez ainda existam recursos vinculados (policies, keys, etc.). Veja a mensagem:" -ForegroundColor Red
    Write-Host $_
    Write-Host "Verifique e repita os passos 1..10 manualmente se necessário."
    exit 1
}

# 12) OPTIONAL: cleanup SecretsManager secret named like albinomarks (safe default: schedule deletion with recovery window)
$secretToCheck = "albinomarks/s3"
try {
    $desc = aws secretsmanager describe-secret --secret-id $secretToCheck --region $Region --output json 2>&1
    if ($desc) {
        Write-Host "Encontrado secret '$secretToCheck'. Agendando exclusão com recovery window de 7 dias (seguro)."
        aws secretsmanager delete-secret --secret-id $secretToCheck --recovery-window-in-days 7 --region $Region
        Write-Host "Secret agendado para exclusão em 7 dias. Se quiser exclusão imediata, use --force-delete-without-recovery (risco)."
    }
} catch {
    Write-Host "Nenhum secret '$secretToCheck' encontrado ou falta de permissão para ver/delete. OK."
}

Write-Host "=== FIM do procedimento ===" -ForegroundColor Cyan
