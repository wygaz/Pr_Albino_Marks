# Projeto Pr. Albino Marks

Este é um sistema web desenvolvido com Django para a publicação de textos do Pr. Albino Marks, reunindo décadas de reflexões, comentários e materiais sobre a Lição da Escola Sabatina.

## 📌 Funcionalidades

- Listagem e leitura de artigos em HTML
- Interface simples e limpa
- Importação automatizada de artigos por planilha Excel
- Upload e associação de imagens ilustrativas aos textos
- Estrutura preparada para crescimento e personalização

## 🚀 Como rodar o projeto

1. Clone o repositório:
   ```bash
   git clone https://github.com/wygaz/Pr_Albino_Marks.git
   cd Pr_Albino_Marks
   ```

2. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Crie um arquivo `.env` com a variável de banco de dados:
   ```
   DATABASE_URL=postgres://postgres:senha@localhost:5432/nome_do_banco
   ```

5. Rode o servidor:
   ```bash
   python manage.py runserver
   ```

## 🧰 Tecnologias utilizadas

- Python 3.12
- Django 4.x
- PostgreSQL
- HTML, CSS
- Pandas (para importação por planilha)
- django-environ e dj-database-url

## ✍️ Contribuições

Contribuições são bem-vindas! Crie um fork, abra uma branch e envie um pull request.  
Ou entre em contato diretamente.

---

📘 Desenvolvido com carinho por **Wanderley Gazeta** para preservar e compartilhar o legado do Pr. Albino Marks.  
🤖 Apoio fundamental: **ChatGPT**

Rodar versão local para HTTPS:
         python manage.py runserver_plus --cert-file localhost.pem --key-file localhost-key.pem