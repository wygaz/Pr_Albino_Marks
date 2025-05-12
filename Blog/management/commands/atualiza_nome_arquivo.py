# A_Lei_no_NT/management/commands/atualiza_nome_arquivo.py

import os
from django.core.management.base import BaseCommand
\l Blog.models import Artigo

class Command(BaseCommand):
    help = 'Atualiza o campo nome_arquivo_txt e ordem dos artigos na base de dados'

    def handle(self, *args, **kwargs):
        base_path = 'C:/Users/Wanderley/Apps/Albino_Marks/media/Txt'
        
        arquivos_no_diretorio = os.listdir(base_path)
        print("Arquivos no diretório:")
        for arquivo in arquivos_no_diretorio:
            print(arquivo)

        print("\nArtigos no banco de dados:")
        for artigo in Artigo.objects.all():
            print(artigo.titulo, artigo.nome_arquivo_txt)

        for arquivo in arquivos_no_diretorio:
            numero = arquivo.split('_')[0]
            if numero.isdigit():
                ordem = int(numero)
                nome_arquivo_txt = arquivo
                artigo = Artigo.objects.filter(nome_arquivo_txt__iexact=nome_arquivo_txt).first()
                if artigo:
                    artigo.ordem = ordem
                    artigo.save()
                    self.stdout.write(self.style.SUCCESS(f'Artigo {artigo.titulo} atualizado com a ordem {artigo.ordem}.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Artigo com arquivo {nome_arquivo_txt} não encontrado no banco de dados.'))
            else:
                self.stdout.write(self.style.WARNING(f'Arquivo {arquivo} não possui um número inicial válido.'))
