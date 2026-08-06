[CmdletBinding()]
param(
  [switch]$SkipFrontend,
  [int]$FrontendPort = 8443
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot 'FigmaMake_UI'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop/CLI is required for the local synthetic demo.' }
if (-not (Test-Path (Join-Path $frontendRoot 'node_modules'))) { throw 'FigmaMake_UI dependencies are missing. Run pnpm install in FigmaMake_UI first.' }
if (-not $env:BRAVO_POSTGRES_HOST_PORT) { $env:BRAVO_POSTGRES_HOST_PORT = '55432' }

$compose = @('-f', 'docker-compose.yml', '-f', 'docker-compose.override.yml', '-f', 'docker-compose.demo18.yml')
Push-Location $repoRoot
try {
  & docker compose @compose up -d --build postgres redis api
  $deadline = (Get-Date).AddSeconds(90)
  $health = $null
  do {
    try {
      $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3
      if ($health.status -eq 'ok') { break }
    } catch { Start-Sleep -Milliseconds 750 }
  } while ((Get-Date) -lt $deadline)
  if (-not $health -or $health.status -ne 'ok') { throw 'Local API did not become healthy. Run docker compose logs api for the startup error.' }
  & docker compose @compose exec -T api sh -lc 'alembic current'
  & docker compose @compose exec -T api sh -lc 'PYTHONPATH=. python scripts/seed_demo.py'
} finally { Pop-Location }

if (-not $SkipFrontend) {
  try { Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$FrontendPort" -TimeoutSec 1 | Out-Null; Write-Host "Frontend already responds on http://127.0.0.1:$FrontendPort" }
  catch {
    $process = Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('run', 'dev', '--', '--port', "$FrontendPort") -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru
    Write-Host "Started FigmaMake UI (PID $($process.Id)) on http://127.0.0.1:$FrontendPort"
  }
}

Write-Host 'Synthetic internal demo is ready. Use /health, sign in with an authorized seeded identity, and keep production/pilot claims disabled.'
