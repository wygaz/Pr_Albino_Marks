# Generated by Django 5.0.6 on 2024-07-07 22:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('A_Lei_no_NT', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_area', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Artigo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('texto', models.TextField()),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='A_Lei_no_NT.area')),
            ],
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_autor', models.CharField(max_length=200)),
                ('biografia', models.TextField()),
                ('midia', models.FileField(blank=True, null=True, upload_to=\1Blog/Imagens/Autores/')),
                ('foto', models.ImageField(blank=True, null=True, upload_to=\1Blog/Imagens/Autores/')),
            ],
        ),
        migrations.CreateModel(
            name='Midia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=50)),
                ('caminho', models.CharField(max_length=200)),
                ('descricao', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Texto',
        ),
        migrations.AddField(
            model_name='artigo',
            name='autor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='A_Lei_no_NT.autor'),
        ),
        migrations.AddField(
            model_name='artigo',
            name='midia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='A_Lei_no_NT.midia'),
        ),
    ]
