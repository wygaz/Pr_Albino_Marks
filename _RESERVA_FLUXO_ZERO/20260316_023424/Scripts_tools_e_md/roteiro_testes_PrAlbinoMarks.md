# 📋 Roteiro de Testes Manuais - Projeto Pr. Albino Marks

**Objetivo:** Revisar o funcionamento atual do site local, para reativar a memória sobre o projeto e definir os próximos passos.

---

## ✅ Instruções gerais

- Execute o servidor com `run.bat` (versão corrigida para `localhost:8000`).
- Acesse o site em: [ 	](https://localhost:8000/)
- Teste cada etapa abaixo e marque com `X` quando concluído.

---

## 1️⃣ Página Inicial (home)

- [ ] O site abre corretamente com HTTPS (cadeado verde).
- [ ] O menu principal (Home, Artigos, Vídeos, Livros) aparece e os links funcionam.

---

## 2️⃣ Página de Artigos (Posts)

- [ ] A página de artigos (`/artigos/` ou `/posts/`) lista os artigos cadastrados.
- [ ] Cada artigo possui:
    - [ ] Título
    - [ ] Data
    - [ ] Pequeno resumo ou início do texto
    - [ ] Link "Ler mais"
- [ ] O link "Ler mais" leva para a página completa do artigo.

---

## 3️⃣ Comentários em Artigos

- [ ] A seção de comentários aparece no final do artigo.
- [ ] É possível postar um novo comentário.
- [ ] O novo comentário aparece corretamente na lista.
- [ ] Verificar se existe campo de resposta (comentários encadeados).
- [ ] Verificar se existe controle de visibilidade (campo `visivel`).
- [ ] Verificar se existe botão de curtida (campo `curtidas`).

---

## 4️⃣ Página de Vídeos

- [ ] A página de vídeos (`/videos/`) lista os vídeos cadastrados.
- [ ] Cada vídeo tem:
    - [ ] Título
    - [ ] Miniatura ou link do vídeo.
- [ ] O vídeo abre corretamente no player ou no link.

---

## 5️⃣ Página de Livros / PDFs

- [ ] A página de livros (`/livros/`) lista os livros cadastrados.
- [ ] Cada livro possui:
    - [ ] Título
    - [ ] Descrição (se houver)
    - [ ] Link para download.
- [ ] O link para o PDF funciona corretamente (abre ou baixa o arquivo).

---

## 6️⃣ Painel Admin

- [ ] A página `/admin/` abre corretamente.
- [ ] O login do admin funciona.
- [ ] No admin, são exibidos:
    - [ ] Posts
    - [ ] Vídeos
    - [ ] Livros
    - [ ] Comentários (com campos `visivel`, `resposta_a`, `curtidas`).
- [ ] É possível moderar um comentário (alterar `visivel`).

---

## Observações gerais

- Anotar qualquer erro ou comportamento inesperado para tratarmos depois.
- Após concluir todos os testes, informar no chat para iniciarmos a próxima etapa: **melhoria da interface de comentários**.

---

