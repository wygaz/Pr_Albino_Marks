def docx_para_html(arquivo):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs
    html = ''
    titulo = ''
    autor = ''

    def detectar_titulo_possivel(paragrafos):
        for p in paragrafos[:5]:
            texto = ''.join(run.text for run in p.runs).strip()
            if texto and len(texto.split()) <= 12 and p.style.name.startswith('Heading'):
                return texto
        return ''

    def detectar_autor(paragrafos):
        for p in paragrafos[:5]:
            texto = ''.join(run.text for run in p.runs).strip()
            if texto.lower().startswith("autor:") or p.alignment == 2:
                nome = texto.replace("Autor:", "").replace("autor:", "").strip()
                if 3 <= len(nome.split()) <= 5:
                    return nome
        return ''

    titulo = detectar_titulo_possivel(paragrafos)
    autor = detectar_autor(paragrafos)

    for p in paragrafos:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto or texto == f"Autor: {autor}" or texto == "Autor:" or texto == titulo:
            continue

        texto_formatado = ''
        for run in p.runs:
            t = run.text.replace('\n', '<br>').replace('\xa0', '&nbsp;')
            if '<w:br w:type="page"/>' in run._element.xml:
                texto_formatado += '<hr class="page-break">'
            if run.bold:
                t = f'<strong>{t}</strong>'
            if run.italic:
                t = f'<em>{t}</em>'
            if run.underline:
                t = f'<u>{t}</u>'
            texto_formatado += t

        estilo_manual = re.match(r"^(\d+[\.\)]|[a-zA-Z][\.\)])\s", texto)
        if p._p.pPr is not None and p._p.pPr.numPr is not None:
            numId = p._p.pPr.numPr.numId.val
            if numId == 1:
                html += f'<ul><li>{texto_formatado}</li></ul>\n'
            elif numId == 2:
                html += f'<ol><li>{texto_formatado}</li></ol>\n'
            else:
                html += f'<p>{texto_formatado}</p>\n'
        elif estilo_manual:
            if estilo_manual.group(1)[0].isdigit():
                html += f'<ol><li>{texto_formatado}</li></ol>\n'
            else:
                html += f'<ul><li>{texto_formatado}</li></ul>\n'
        else:
            html += f'<p>{texto_formatado}</p>\n'

    for tabela in doc.tables:
        html += '<table border="1" style="border-collapse: collapse; margin-top: 1em;">'
        for linha in tabela.rows:
            html += '<tr>'
            for celula in linha.cells:
                conteudo = '<br>'.join(p.text for p in celula.paragraphs)
                html += f'<td style="padding: 4px;">{conteudo}</td>'
            html += '</tr>'
        html += '</table>'

    soup = BeautifulSoup(html, 'html.parser')
    novas_tags = []
    lista_atual = []
    tipo_lista = None

    for el in soup.contents:
        if el.name in ['ul', 'ol']:
            if tipo_lista == el.name:
                lista_atual.extend(el.find_all('li'))
            else:
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                tipo_lista = el.name
                lista_atual = el.find_all('li')
        else:
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None
            novas_tags.append(el)

    if lista_atual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    return str(soup), titulo, autor