# Infraestrutura — Projeto Pr. Albino Marks

> Documento de referência rápida para quem configura, opera ou dá suporte ao projeto.
> **Não** coloque segredos aqui (use `.env` / variáveis do provedor).  
> Última revisão: ___/___/____

---

## 1) Visão geral

- **App**: Django + Postgres + Storage S3 (media)  
- **Ambientes**:  
  - **Local**: desenvolvimento em máquina do dev  
  - **Produção**: Railway (app + banco), S3 para media
- **Padrão para arquivos**: todo **MEDIA** em S3, sem conversão DOCX→PDF no servidor; PDF é gerado localmente e publicado.

---

## 2) Banco de Dados (PostgreSQL)

### Criação (exemplo)
Crie o banco e um usuário dedicado para o Django (no *cluster* Postgres):
```sql
CREATE DATABASE "AlbinoMarks";
CREATE USER albino_django WITH PASSWORD 'SUA_SENHA_SEGURA';
GRANT ALL PRIVILEGES ON DATABASE "AlbinoMarks" TO albino_django;
