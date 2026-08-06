$ErrorActionPreference = 'Stop'
$port = 4317
$node = (Get-Command node.exe -ErrorAction Stop).Source
$vite = Start-Process -FilePath $node -ArgumentList '.\node_modules\vite\bin\vite.js', '--host', '127.0.0.1', '--port', $port -WorkingDirectory $PSScriptRoot\.. -WindowStyle Hidden -PassThru

try {
  $deadline = (Get-Date).AddSeconds(30)
  do {
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port" -TimeoutSec 1
      if ($response.StatusCode -ge 200) { break }
    } catch { Start-Sleep -Milliseconds 250 }
  } while ((Get-Date) -lt $deadline)
  if ((Get-Date) -ge $deadline) { throw 'Vite did not become ready for Playwright.' }

  $env:PLAYWRIGHT_EXTERNAL_SERVER = '1'
  $env:PLAYWRIGHT_BASE_URL = "http://127.0.0.1:$port"
  & $node '.\node_modules\@playwright\test\cli.js' test @args
  exit $LASTEXITCODE
} finally {
  if (-not $vite.HasExited) { Stop-Process -Id $vite.Id -Force }
}
