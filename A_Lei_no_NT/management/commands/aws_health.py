# A_Lei_no_NT/management/commands/aws_health.py
import os
from django.core.management.base import BaseCommand
import boto3
from botocore.exceptions import ClientError

def _client(service):
    return boto3.client(
        service_name=service,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")  # se estiver usando STS
    )

class Command(BaseCommand):
    help = "Verifica credenciais AWS e acesso ao S3 (whoami + list prefix)."

    def handle(self, *args, **opts):
        try:
            sts = _client("sts").get_caller_identity()
            self.stdout.write(self.style.SUCCESS(f"Identidade: {sts}"))
        except ClientError as e:
            self.stderr.write(self.style.ERROR(f"STS falhou: {e}"))
            return

        bucket = os.getenv("S3_BUCKET_NAME")
        prefix = "secrets/users/"

        try:
            s3 = _client("s3")
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            keys = [c["Key"] for c in resp.get("Contents", [])]
            self.stdout.write(self.style.SUCCESS(f"S3 OK - {bucket}/{prefix} (amostra): {keys[:5]}"))
        except ClientError as e:
            self.stderr.write(self.style.ERROR(f"S3 falhou: {e}"))