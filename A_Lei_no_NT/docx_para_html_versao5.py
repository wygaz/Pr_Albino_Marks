def docx_para_html(arquivo):
    document = Document(arquivo)
    html = ''
    titulo_extraido = ''
    buffer_paragrafo = None

    for paragrafo in document.paragraphs:
        texto = paragrafo.text.strip()

        if not texto:
            html += '<br>'
            continue

        estilo = paragrafo.style.name if paragrafo.style else ''
        if estilo.startswith('Heading') and not titulo_extraido:
            titulo_extraido = texto

        if buffer_paragrafo:
            texto = buffer_paragrafo + ' ' + texto
            buffer_paragrafo = None

        if texto.strip().endswith(':'):
            html += f'<p><strong>{texto}</strong></p>'
            continue

        if texto.strip().endswith('.') and texto.strip()[:-1].isdigit():
            buffer_paragrafo = texto
            continue

        if any(run.bold for run in paragrafo.runs):
            partes = []
            for run in paragrafo.runs:
                txt = run.text
                if run.bold:
                    txt = f'<strong>{txt}</strong>'
                elif run.italic:
                    txt = f'<em>{txt}</em>'
                elif run.underline:
                    txt = f'<u>{txt}</u>'
                partes.append(txt)
            html += f"<p>{''.join(partes)}</p>"
        else:
            html += f'<p>{texto}</p>'

    soup = BeautifulSoup(html, 'html.parser')
    novas_tags = []
    lista_atual = []
    tipo_lista = None

    for tag in soup.contents:
        if tag.name == 'p' and tag.text.strip().startswith(('-', '*')):
            if tipo_lista != 'ul':
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                    lista_atual = []
                tipo_lista = 'ul'
            li = soup.new_tag('li')
            li.string = tag.text.strip()[1:].strip()
            lista_atual.append(li)
        elif tag.name == 'p' and tag.text.strip()[0:2].isdigit() and tag.text.strip()[2:3] == '.':
            if tipo_lista != 'ol':
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                    lista_atual = []
                tipo_lista = 'ol'
            li = soup.new_tag('li')
            li.string = tag.text.strip()[3:].strip()
            lista_atual.append(li)
        else:
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None
            novas_tags.append(tag)

    if lista_atual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    if not titulo_extraido:
        titulo_extraido = "Artigo sem Título"

    return str(soup), titulo_extraido