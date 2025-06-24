# 🛠️ Passo-a-Passo — Adicionar certificado local como confiável no Windows

## 1️⃣ Preparar o arquivo .crt

- Copie o arquivo `certificado.pem` para a área de trabalho.
- Renomeie o arquivo para `certificado.crt`.

## 2️⃣ Abrir o Gerenciador de Certificados do Windows

- Pressione `Win + R`, digite `certmgr.msc`, clique em OK.

## 3️⃣ Importar o certificado

- Vá em: `Autoridades de Certificação Raiz Confiáveis → Certificados`.
- Clique com o botão direito em `Certificados → Todas as Tarefas → Importar...`.
- Avance → escolha `certificado.crt`.
- Avance → selecione "Autoridades de Certificação Raiz Confiáveis".
- Concluir.

## 4️⃣ Reiniciar o navegador

- Feche totalmente o Chrome (inclusive da bandeja).
- Abra novamente e acesse `https://localhost:8000/`.
- O certificado será aceito sem erro.

## Observação

- Você só precisará refazer se gerar um novo certificado diferente.
- Em produção (Railway), usará Let's Encrypt — sem este processo.

