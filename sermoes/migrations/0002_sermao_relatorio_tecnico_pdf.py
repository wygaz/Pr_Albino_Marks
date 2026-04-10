# Generated manually for technical-report field support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sermoes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sermao",
            name="relatorio_tecnico_pdf",
            field=models.FileField(blank=True, null=True, upload_to="pdfs/relatorios_tecnicos/"),
        ),
    ]
