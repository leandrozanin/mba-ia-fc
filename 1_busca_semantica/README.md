# Busca semântica em PDF

Projeto Python que lê um PDF, divide o texto em trechos, armazena os embeddings no PostgreSQL com pgvector e permite fazer perguntas pelo terminal. As respostas devem usar somente o conteúdo recuperado do documento.

## Pré-requisitos

- Python 3.10 ou superior
- Docker Desktop com Docker Compose
- Uma chave da API da OpenAI

## 1. Preparar o ambiente

Abra o terminal nesta pasta (`1_busca_semantica`) e crie um ambiente virtual:

```powershell
python -m venv .venv
```

Ative o ambiente no Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

No macOS ou Linux, use:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## 2. Configurar as variáveis

Crie o arquivo `.env` a partir do modelo:

```powershell
Copy-Item .env.example .env
```

No macOS ou Linux, o comando equivalente é `cp .env.example .env`. Abra `.env` e substitua `OPENAI_API_KEY` pela sua chave da API. O arquivo também permite configurar:

- `OPENAI_EMBEDDING_MODEL` e `OPENAI_EMBEDDING_DIMENSIONS`: modelo e dimensão dos vetores;
- `OPENAI_CHAT_MODEL`: modelo usado para escrever as respostas;
- `PDF_PATH`: caminho do PDF a ingerir (por padrão, `./document.pdf`);
- `DATABASE_URL` e as variáveis `POSTGRES_*`: conexão e credenciais do banco;
- `PGVECTOR_COLLECTION`: nome da collection onde os vetores serão guardados.

O projeto inclui `document.pdf`, uma cópia do material de fundamentos de IA que acompanha o desafio. Para usar outro documento, substitua esse arquivo ou altere `PDF_PATH` no `.env`.

Use o mesmo modelo e dimensão de embeddings na ingestão e nas consultas. Se trocar algum deles depois da ingestão, apague os dados do banco e ingira o PDF novamente.

## 3. Iniciar o banco de dados

Na pasta do projeto, execute:

```powershell
docker compose up -d --wait
```

Esse comando inicia o PostgreSQL com a extensão pgvector e aguarda o banco ficar pronto.

## 4. Ingerir o PDF

Com o ambiente virtual ativo e o banco ligado, execute:

```powershell
python src/ingest.py
```

O script divide o texto em chunks de 1.000 caracteres com overlap de 150, gera os embeddings e grava os trechos no banco. Cada nova ingestão substitui o conteúdo anterior da collection.

## 5. Fazer perguntas

Inicie o chat:

```powershell
python src/chat.py
```

Digite sua pergunta após `PERGUNTA:`. O sistema busca até 10 trechos relevantes e usa a LLM para responder com base neles. Digite `sair` para encerrar. Quando os trechos não contiverem a resposta, o chat deve responder:

> Não tenho informações necessárias para responder sua pergunta.

## Encerrar ou reiniciar

Para parar o banco e preservar os dados:

```powershell
docker compose down
```

Para apagar também os dados armazenados e começar de novo:

```powershell
docker compose down -v
```
