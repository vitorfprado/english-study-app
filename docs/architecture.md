# Arquitetura MVP

## Visao geral

Internet -> EC2 publica -> Caddy -> Next.js -> PostgreSQL (container interno)

## Principios

- Custo minimo: EC2 unica, sem servicos gerenciados pagos no inicio.
- Simplicidade: Docker Compose para subir app + banco + proxy.
- Evolucao: camadas separadas para IA, regras de revisao e infraestrutura.

## Componentes

- `app`: frontend + backend API em Next.js (App Router).
- `postgres`: persistencia de decks, cards, revisoes e logs de uso de IA.
- `caddy`: reverse proxy e HTTPS automatizado quando houver dominio.
- `infra`: Terraform para VPC, subnet publica, SG, EC2, IAM e S3.

## Fluxo de revisao

1. Buscar card pendente (`next_review_at <= now`).
2. Usuario responde em ingles.
3. Validacao local simples (normalizacao + similaridade).
4. Se duvida, chamar IA para decisao e explicacao.
5. Salvar Review e atualizar proxima revisao do Card.
