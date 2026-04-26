# English Study App

Aplicacao pessoal para estudar ingles com repeticao espacada simples e suporte de IA para geracao de cards e correcao de respostas.

## Objetivo

Entregar um MVP simples, barato e facil de evoluir:
- criar decks;
- gerar cards com IA;
- revisar traducoes;
- corrigir respostas com validacao local + IA quando necessario;
- salvar historico e proxima revisao.

## Arquitetura

Internet -> EC2 publica -> Caddy -> Next.js + Prisma -> PostgreSQL (container interno)

Detalhes em `docs/architecture.md`.

## Estrutura

- `app`: aplicacao Next.js fullstack.
- `deploy`: `docker-compose.yml`, `Caddyfile`, scripts de backup/restore.
- `infra`: Terraform para AWS (VPC, SG, EC2, IAM, S3).
- `docs`: arquitetura e roadmap.

## Variaveis de ambiente

Crie um arquivo `.env` na raiz a partir do `.env.example`.

Linux/macOS:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Preencha principalmente:
- `DATABASE_URL`
- `CLAUDE_API_KEY`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `AWS_REGION`, `S3_BACKUP_BUCKET`

## Rodando localmente (100% em container)

> Fluxo recomendado para testes: sem Node instalado localmente.

1. Instale apenas Docker Desktop (ou Docker Engine + Compose plugin).
2. Crie o `.env` na raiz do projeto.
3. Garanta que `DATABASE_URL` use o host `postgres` (servico do Compose), por exemplo:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/english_study
```

4. Suba os containers:

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

5. Execute as migracoes dentro do container da aplicacao:

```bash
docker exec -it english-study-app npx prisma migrate deploy
```

6. (Opcional, primeira vez) Se ainda nao houver migration criada no projeto:

```bash
docker exec -it english-study-app npx prisma migrate dev --name init
```

7. Acesse localmente:

- App: `http://localhost`
- Se quiser bypass do proxy: `http://localhost:3000` (ajustando expose/port no compose)

### Comandos uteis de teste local

```bash
# logs
docker compose -f deploy/docker-compose.yml logs -f

# parar containers
docker compose -f deploy/docker-compose.yml down

# parar e remover volumes (limpar banco local)
docker compose -f deploy/docker-compose.yml down -v
```

## Deploy na EC2

1. Provisione infraestrutura via Terraform em `infra/`.
2. Conecte na EC2 via SSH.
3. Clone o repositorio.
4. Crie `.env` com valores de producao.
5. Rode `docker compose -f deploy/docker-compose.yml up --build -d`.

## Terraform (infra basica)

Dentro de `infra/`:

```bash
terraform init
terraform plan \
  -var="ami_id=ami-xxxxxxxx" \
  -var="key_name=sua-chave" \
  -var="allowed_ssh_cidr=SEU_IP/32"
terraform apply \
  -var="ami_id=ami-xxxxxxxx" \
  -var="key_name=sua-chave" \
  -var="allowed_ssh_cidr=SEU_IP/32"
```

## Backup e restore

Backup:

```bash
cd deploy/scripts
POSTGRES_USER=postgres POSTGRES_DB=english_study S3_BACKUP_BUCKET=seu-bucket ./backup-db.sh
```

Restore (arquivo local ou S3):

```bash
cd deploy/scripts
POSTGRES_USER=postgres POSTGRES_DB=english_study ./restore-db.sh ./backups/db-20260101-120000.sql.gz
```

## Decisoes arquiteturais

- Sem EKS/ECS/RDS/LB no MVP para reduzir custo.
- Postgres em container privado no mesmo host da app.
- Camada de IA isolada em `app/src/services/ai`.
- Repeticao espacada inicial simples e extensivel.

## Cuidados de custo

- EC2 pequena (`t3.micro` ou equivalente elegivel).
- Sem NAT Gateway, sem Load Balancer, sem CloudFront no MVP.
- Chamadas de IA somente para geracao de cards e revisoes duvidosas.

## Roadmap

Veja `docs/roadmap.md`.
