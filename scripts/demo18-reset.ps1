[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $env:BRAVO_POSTGRES_HOST_PORT) { $env:BRAVO_POSTGRES_HOST_PORT = '55432' }
$compose = @('-f', 'docker-compose.yml', '-f', 'docker-compose.override.yml', '-f', 'docker-compose.demo18.yml')

Push-Location $repoRoot
try {
  & docker compose @compose exec -T api sh -lc 'PYTHONPATH=. python scripts/seed_demo.py'
} finally { Pop-Location }

Write-Host 'Synthetic demo identities and their least-privilege capabilities were re-seeded. Existing conversations, uploads, and cases were intentionally retained; this command never deletes shared/local user data.'
