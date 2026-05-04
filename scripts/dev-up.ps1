# Sobe Docker Compose e aplica migrations (Alembic).
# Uso (na raiz do repo): powershell -ExecutionPolicy Bypass -File scripts\dev-up.ps1
# Mensagens em ASCII para evitar erro de parsing no Windows PowerShell 5.1 sem UTF-8 BOM.

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    Write-Host '[dev-up] .env missing - copying from .env.example'
    Copy-Item (Join-Path $RepoRoot ".env.example") (Join-Path $RepoRoot ".env")
}

Write-Host '[dev-up] docker compose up --build -d --remove-orphans'
docker compose up --build -d --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Host "[dev-up] error: docker compose failed (exit code $LASTEXITCODE)."
    Write-Host '[dev-up] hint: if port 8000 is in use, run: docker compose down --remove-orphans'
    Write-Host '[dev-up] hint: then list containers: docker ps -a'
    exit $LASTEXITCODE
}

Write-Host '[dev-up] waiting for Alembic (retries if web container is still starting)...'
$ok = $false
for ($i = 1; $i -le 10; $i++) {
    docker compose exec -T web alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        $ok = $true
        break
    }
    Write-Host "[dev-up] attempt $i failed (exit $LASTEXITCODE), sleeping 3s..."
    Start-Sleep -Seconds 3
}

if (-not $ok) {
    Write-Host '[dev-up] error: alembic upgrade head did not finish. Try: docker compose logs web'
    exit 1
}

Write-Host '[dev-up] done. App: http://localhost:8000'
