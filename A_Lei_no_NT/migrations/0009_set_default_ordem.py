from django.db import migrations

def set_default_ordem(apps, schema_editor):
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')
    for index, artigo in enumerate(Artigo.objects.all(), start=1):
        if artigo.ordem is None:
            artigo.ordem = index
            artigo.save()

class Migration(migrations.Migration):

    dependencies = [
        ('A_Lei_no_NT', '0008_remove_artigo_caminho_arquivo_docx_and_more'),
    ]

    operations = [
        migrations.RunPython(set_default_ordem),
    ]
