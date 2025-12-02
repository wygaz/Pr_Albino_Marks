import os
import io
import email
import docx
import pandas as pd
from imapclient import IMAPClient
from datetime import datetime, date
from pathlib import Path
import unicodedata
import re

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)

EMAIL_USER = "wygazeta@gmail.com"

# >>> Lê a senha do Gmail da variável de ambiente
EMAIL_PASS = os.environ.get("GMAIL_ALBINO_APP_PASS")

if not EMAIL_PASS:
    raise RuntimeError(
        "A variável de ambiente GMAIL_ALBINO_APP_PASS não está definida. "
        "Crie a variável no Windows com a senha de app do Gmail."
    )

REMETENTE = "pralbino@gmail.com"
DATA_INICIO = date(2025, 11, 25)
PASTA_SAIDA = Path(
    "C:/Users/Wanderley/Apps/Pr_Albino_Marks_restaurado/Apenas_Local/anexos_filtrados"
)
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

print("🔐 Conectando ao servidor IMAP...")
with IMAPClient("imap.gmail.com") as server:
    server.login(EMAIL_USER, EMAIL_PASS)
    server.select_folder("INBOX")

    # IMAP espera o mês em inglês, ex: 25-Nov-2025
    data_limite = DATA_INICIO.strftime("%d-%b-%Y")
    mensagens = server.search(["FROM", REMETENTE, "SINCE", data_limite])

    print(f"📨 Total de e-mails encontrados: {len(mensagens)}")
    resultados: list[dict[str, str]] = []

    fetched = server.fetch(mensagens, ["RFC822", "INTERNALDATE"])

    for uid, mensagem_data in fetched.items():
        # -------- Corpo bruto do e-mail --------
        raw_email = mensagem_data.get(b"RFC822")
        if not isinstance(raw_email, (bytes, bytearray)):
            # Em princípio não deve acontecer, mas evita erro em tempo de execução
            continue

        msg = email.message_from_bytes(raw_email)

        # -------- Data do e-mail --------
        internal_date = mensagem_data.get(b"INTERNALDATE")

        if isinstance(internal_date, datetime):
            data_email = internal_date.date()
        else:
            # Fallback simples, caso o tipo venha diferente do esperado
            try:
                if isinstance(internal_date, (bytes, bytearray)):
                    internal_date_str = internal_date.decode(errors="ignore")
                else:
                    internal_date_str = str(internal_date)
                data_email = datetime.strptime(
                    internal_date_str[:16], "%d-%b-%Y %H:%M"
                ).date()
            except Exception:
                data_email = DATA_INICIO

        # Garantia extra: pula qualquer coisa antes da DATA_INICIO
        if data_email < DATA_INICIO:
            continue

        # -------- Texto do e-mail (opcional) --------
        corpo_email: str | None = None
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, (bytes, bytearray)):
                    corpo_email = payload.decode(errors="ignore").strip()
                break

        # -------- Varre anexos DOCX --------
        for part in msg.walk():
            if (
                part.get_content_type()
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                conteudo = part.get_payload(decode=True)
                if not isinstance(conteudo, (bytes, bytearray)):
                    continue

                doc = docx.Document(io.BytesIO(conteudo))
                paragrafos = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

                titulo = paragrafos[0] if len(paragrafos) > 0 else "Sem título"
                autor = paragrafos[1] if len(paragrafos) > 1 else "Pr. Albino Marks"
                slug = slugify(titulo)

                nome_base = f"{data_email.isoformat()} {titulo}".strip()
                # Remove caracteres proibidos em nomes de arquivos do Windows
                nome_base_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_base)
                nome_arquivo = f"{nome_base_limpo}.docx"
                caminho_arquivo = PASTA_SAIDA / nome_arquivo

                # Evita sobrescrever se já existir
                contador = 1
                while caminho_arquivo.exists():
                    caminho_arquivo = (
                        PASTA_SAIDA / f"{nome_base_limpo}_{contador}.docx"
                    )
                    contador += 1

                with open(caminho_arquivo, "wb") as f:
                    f.write(conteudo)

                resultados.append(
                    {
                        "Data": data_email.isoformat(),
                        "Título": titulo,
                        "Autor": autor,
                        "Slug": slug,
                        "Arquivo": str(caminho_arquivo),
                        "Corpo do e-mail": corpo_email or "",
                    }
                )

if resultados:
    df = pd.DataFrame(resultados)
    caminho_csv = PASTA_SAIDA / "anexos_filtrados_com_dados.csv"
    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Arquivos salvos em: {PASTA_SAIDA}")
    print(f"📁 Dados exportados para: {caminho_csv}")
else:
    print("ℹ️ Nenhum anexo DOCX encontrado no período especificado.")
