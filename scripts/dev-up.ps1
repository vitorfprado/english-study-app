# Sobe Docker Compose e aplica migrations (Alembic).
# Uso (na raiz do repo): powershell -ExecutionPolicy Bypass -File scripts\dev-up.ps1

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    Write-Host "[dev-up] .env não encontrado — copiando de .env.example"
    Copy-Item (Join-Path $RepoRoot ".env.example") (Join-Path $RepoRoot ".env")
}

Write-Host "[dev-up] docker compose up -d --build"
docker compose up -d --build

Write-Host "[dev-up] aguardando Alembic (retries se o container ainda estiver iniciando)..."
$ok = $false
for ($i = 1; $i -le 10; $i++) {
    docker compose exec -T app alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        $ok = $true
        break
    }
    Write-Host "[dev-up] tentativa $i falhou (código $LASTEXITCODE), aguardando 3s..."
    Start-Sleep -Seconds 3
}

if (-not $ok) {
    Write-Host "[dev-up] erro: alembic upgrade head não concluiu. Veja: docker compose logs app"
    exit 1
}

Write-Host "[dev-up] pronto. App: http://localhost:8000"
