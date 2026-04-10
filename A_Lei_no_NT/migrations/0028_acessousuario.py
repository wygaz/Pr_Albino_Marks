# Generated manually for access-control infrastructure.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("A_Lei_no_NT", "0027_artigo_views_alter_artigo_slug"),
    ]

    operations = [
        migrations.CreateModel(
            name="AcessoUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("termos_aceitos", models.BooleanField(default=False)),
                ("lgpd_aceita", models.BooleanField(default=False)),
                ("termos_versao", models.CharField(default="v1", max_length=32)),
                ("lgpd_versao", models.CharField(default="v1", max_length=32)),
                ("aceite_realizado_em", models.DateTimeField(blank=True, null=True)),
                ("habilitado_em", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="acesso_site",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Acesso de usuario",
                "verbose_name_plural": "Acessos de usuarios",
            },
        ),
    ]
