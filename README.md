# English Study App

MVP pessoal para estudar inglês com **materiais**, **exercícios**, **respostas com feedback** e **sessões de estudo**. Tudo roda **100% local** com **Docker Compose** (FastAPI + PostgreSQL + Jinja2 + HTMX).

Não há Terraform, Ansible, Kubernetes, CI/CD nem autenticação neste estágio.

## Objetivo

- Cadastrar textos, resumos e materiais em inglês.
- Criar exercícios manualmente ou com auxílio de IA (com **fallback mock** quando não houver chave de API).
- Responder exercícios e ver correção e explicação curta.
- Registrar sessões de estudo (início/fim).

## Stack

- Python 3.12, FastAPI, Uvicorn  
- PostgreSQL 16  
- SQLModel, Alembic  
- Jinja2, HTMX, CSS simples  
- Integração opcional com API de IA (`openai` ou `anthropic`) via variáveis de ambiente  

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
| `AI_API_KEY` / `AI_PROVIDER` | Opcionais; vazios = gerador local (mock) |
| `AI_PROVIDER` | `openai` ou `anthropic` quando usar IA real |
| `AI_MODEL` | Ex.: `gpt-4o-mini` ou `claude-3-5-haiku-20241022` |

## Subir com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build -d
```

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
│   ├── services/         # IA, geração de exercício, correção, sessões
│   ├── templates/        # Jinja2
│   └── static/           # CSS / JS
├── alembic/
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
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
