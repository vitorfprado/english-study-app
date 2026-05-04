# English Study App

MVP pessoal para estudar inglês com **materiais**, **exercícios**, **respostas com feedback** e **sessões de estudo**. Roda com **Docker Compose** (FastAPI + PostgreSQL + Jinja2 + HTMX), com imagem publicada no Docker Hub via CI.

Não há Terraform, Ansible, Kubernetes nem autenticação neste estágio.

## Objetivo

- Cadastrar textos, resumos e materiais em inglês.
- **Importar PDF** do resumo da aula: extração de texto no servidor (`pypdf`), material com `source_type=class_summary`.
- Gerar **decks** de exercícios com IA ou **mock local** se não houver API key, escolhendo na hora da criação: **nome do deck**, **nível**, **tipo de exercício** (fixo ou `mixed`) e quantidade.
- **Estudar um deck numa sessão** (`/study/decks/{id}/start`): fila contínua; ao errar, o cartão volta depois de outros (aprendizado); ao acertar, sai da fila da sessão. Cada resposta atualiza **SRS** simples (próxima revisão em `exercise_srs`).
- Responder exercícios avulsos na página do exercício (histórico) ou dentro da sessão de deck.
- Registrar sessões de estudo legadas (início/fim) em `/study-sessions`.

## Stack

- Python 3.12, FastAPI, Uvicorn  
- PostgreSQL 16  
- SQLModel, Alembic  
- Jinja2, HTMX, CSS simples  
- Integração opcional com API de IA (`openai` ou `anthropic`) via variáveis de ambiente  
- `pypdf` para leitura de PDF  

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ou Docker Engine + plugin Compose)

## Configuração do `.env`

Na raiz do repositório:

**Linux / macOS**

```bash
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

Ajuste principalmente:

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | No Compose, use o host **`db`** (nome do serviço), ex.: `postgresql://postgres:postgres@db:5432/english_study` |
| `POSTGRES_*` | Devem ser coerentes com o usuário/senha na URL |
| `DOCKERHUB_USERNAME` | Seu usuário no Docker Hub (usado pelo `docker-compose.yml`) |
| `APP_VERSION` | Tag da imagem da app (ex.: `latest`, `build-42`, `v0.0.1`) |
| `AI_API_KEY` / `AI_PROVIDER` | Opcionais; vazios = gerador local (mock) e **correção de respostas só por regras locais** |
| `USE_AI_CORRECTION` | `true` (padrão): com IA configurada, a correção de cada resposta usa a API com prompt enxuto (`max_tokens` ~280) |
| `AI_PROVIDER` | `openai` ou `anthropic` quando usar IA real |
| `AI_MODEL` | Ex.: `gpt-4o-mini` ou `claude-3-5-haiku-20241022` |
| `UPLOAD_DIR`, `MAX_PDF_BYTES`, `MAX_EXTRACTED_CHARS`, `DEFAULT_DECK_SIZE`, `MAX_DECK_SIZE` | Opcionais; veja `app/core/config.py` |

PDFs só com **texto selecionável** funcionam bem; PDF escaneado (imagem) exigiria OCR (não incluído neste MVP). Os arquivos ficam em `uploads/` e o `docker-compose.yml` já persiste esse diretório no volume nomeado `uploads_data`.

## CI de imagem Docker (Docker Hub)

O workflow em `.github/workflows/docker-publish.yml` faz build e push da imagem da app para o Docker Hub quando houver push na branch `main` ou em tags `v*.*.*`.

Configure os secrets do repositório no GitHub:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (token de acesso do Docker Hub)

Tags geradas automaticamente por build:

- `latest` (somente na branch padrão)
- `sha-<commit>`
- `build-<run_number>`
- `<YYYYMMDD>-<run_number>`
- `vX.Y.Z` e `X.Y` (quando o push for de tag semântica como `v0.0.1`)

## Subir com Docker Compose

Na raiz do projeto:

```bash
docker compose up -d
```

### Script de inicialização (Compose + migrations)

Na raiz do repositório, em um terminal:

**Linux / macOS**

```bash
bash scripts/dev-up.sh
```

(opcional: `chmod +x scripts/dev-up.sh` e então `./scripts/dev-up.sh`)

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev-up.ps1
```

O script copia `.env.example` → `.env` se não existir, sobe `docker compose up -d` e roda `alembic upgrade head` no container `app` (com retentativas).

No **Windows PowerShell 5.1**, scripts `.ps1` em UTF-8 **sem BOM** com acentos podem falhar ao analisar (`TerminatorExpectedAtEndOfString`). O `dev-up.ps1` usa mensagens ASCII para evitar isso; no **PowerShell 7+** também funciona.

## Migrations (Alembic)

Após o banco estar saudável, aplique as migrations **dentro do container da app**:

```bash
docker compose exec app alembic upgrade head
```

### Criar uma nova migration (após alterar modelos)

```bash
docker compose exec app alembic revision --autogenerate -m "descricao_curta"
docker compose exec app alembic upgrade head
```

Revise o arquivo gerado em `alembic/versions/` antes de commitar.

## Acessar a aplicação

- **App:** [http://localhost:8000](http://localhost:8000)

## Parar os containers

```bash
docker compose down
```

## Limpar volumes locais (apaga dados do PostgreSQL)

```bash
docker compose down -v
```

## Estrutura de pastas

```text
english-study-app/
├── app/
│   ├── main.py
│   ├── deps.py
│   ├── api/routes/       # Rotas HTTP (HTML / HTMX)
│   ├── core/             # Config, logging
│   ├── db/               # Engine, sessão, base para Alembic
│   ├── models/           # Entidades SQLModel
│   ├── schemas/          # Validação Pydantic (form/API)
│   ├── services/         # IA, PDF, geração de exercício/deck, correção, sessões
│   ├── templates/        # Jinja2
│   └── static/           # CSS / JS
├── alembic/
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── uploads/              # PDFs importados (criado em runtime; não versionado)
└── README.md
```

## Comandos úteis

```bash
# Logs em tempo real
docker compose logs -f app

# Shell no container da app
docker compose exec app bash

# Rodar Alembic history
docker compose exec app alembic history
```

## Desenvolvimento sem Docker (opcional)

Com Python 3.12+ e PostgreSQL local:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Defina `DATABASE_URL` apontando para o Postgres local, depois:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Próximos passos possíveis

- Revisão espaçada e flashcards  
- Upload de arquivos (PDF, áudio)  
- Autenticação se deixar de ser só uso local  
- Métricas de progresso e dashboards  
- CI/CD e deploy em nuvem (quando você quiser)  

## Licença

Uso pessoal; ajuste conforme sua necessidade.
