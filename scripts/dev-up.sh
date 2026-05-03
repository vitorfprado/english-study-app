#!/usr/bin/env bash
# Sobe Docker Compose e aplica migrations (Alembic).
# Uso: na raiz do repo: bash scripts/dev-up.sh   ou   ./scripts/dev-up.sh (após chmod +x)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "[dev-up] .env não encontrado — copiando de .env.example"
  cp .env.example .env
fi

echo "[dev-up] docker compose up -d --build"
docker compose up -d --build

echo "[dev-up] aguardando Alembic (retries se o container ainda estiver iniciando)..."
ok=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  if docker compose exec -T app alembic upgrade head; then
    ok=1
    break
  fi
  echo "[dev-up] tentativa $i falhou, aguardando 3s..."
  sleep 3
done

if [[ "$ok" -ne 1 ]]; then
  echo "[dev-up] erro: alembic upgrade head não concluiu. Veja: docker compose logs app"
  exit 1
fi

echo "[dev-up] pronto. App: http://localhost:8000"
