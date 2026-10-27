<#
.SYNOPSIS
  VoltGuard AI R0 tasks for Windows (same targets as the Makefile).

.EXAMPLE
  .\make.ps1 demo
  .\make.ps1 ingest -Dataset tnb_extract_2026_10
  .\make.ps1 test -Local          # run with .\.venv instead of the api container
#>
param(
    [Parameter(Position = 0)][string]$Target = "help",
    [string]$Dataset = "",
    [switch]$Local
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-Py([string[]]$CliArgs) {
    if ($Local) {
        $CliArgs = $CliArgs | ForEach-Object { $_ -replace '^/app/', '../' }
        Push-Location backend
        try { & ..\.venv\Scripts\python.exe @CliArgs; if ($LASTEXITCODE) { throw "python exited with $LASTEXITCODE" } }
        finally { Pop-Location }
    } else {
        docker compose run --rm api python @CliArgs
        if ($LASTEXITCODE) { throw "docker compose run exited with $LASTEXITCODE" }
    }
}

function New-Secret {
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

function Invoke-Setup {
    if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env from .env.example" }
    $text = Get-Content .env -Raw
    foreach ($key in "POSTGRES_PASSWORD", "APP_DB_PASSWORD", "POWERBI_DB_PASSWORD", "JWT_SECRET") {
        if ($text -match "(?m)^$key=\s*(#.*)?$") {
            $text = $text -replace "(?m)^$key=\s*(#.*)?$", "$key=$(New-Secret)"
            Write-Host "Generated $key"
        }
    }
    if ($Local) {
        $text = $text -replace "(?m)^DATA_ROOT=.*$", "DATA_ROOT=./.data"
        $text = $text -replace "(?m)^LLM_MODE=.*$", "LLM_MODE=mock"
    }
    Set-Content .env $text -NoNewline
    $root = ((Get-Content .env | Where-Object { $_ -match "^DATA_ROOT=" }) -replace "^DATA_ROOT=", "" -replace "\s+#.*$", "").Trim()
    foreach ($sub in "raw\london", "raw\sgcc", "raw\datagovmy", "processed", "uploads", "simulated", "photos", "pdfs", "logs", "audit_anchor", "mlruns", "models\ollama", "models\hf") {
        New-Item -ItemType Directory -Force -Path (Join-Path $root $sub) | Out-Null
    }
    Copy-Item data\uploads\README.md (Join-Path $root "uploads\README.md") -Force
    Write-Host "DATA_ROOT ready at $root"
}

function Invoke-Tunnel([string]$Mode) {
    if ($Mode -eq "quick") {
        $running = docker compose ps --status running --services 2>$null | Select-String -SimpleMatch "tunnel"
        if ($running) {
            Write-Warning "A quick tunnel is already running. Restarting it would change the address and break saved phone sign-ins, offline cases and every Telegram link already sent. Not restarting."
        } else {
            docker compose --profile tunnel up -d tunnel
        }
        $url = $null
        foreach ($i in 1..30) {
            $url = (docker compose --profile tunnel logs tunnel 2>&1 | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches |
                    ForEach-Object { $_.Matches.Value } | Select-Object -Last 1)
            if ($url) { break }
            Start-Sleep -Seconds 2
        }
        if (-not $url) { throw "No tunnel address yet; check: docker compose --profile tunnel logs tunnel" }
    } else {
        if (-not (Test-Path deploy\cloudflared\config.yml)) { throw "Copy deploy\cloudflared\config.example.yml to config.yml and fill it in first." }
        docker compose --profile tunnel-named up -d tunnel-named
        $hostLine = (Get-Content .env | Where-Object { $_ -match "^TUNNEL_HOSTNAME=" }) -replace "^TUNNEL_HOSTNAME=", ""
        $url = "https://$($hostLine.Trim())"
    }
    $text = Get-Content .env -Raw
    $text = $text -replace "(?m)^PUBLIC_BASE_URL=.*$", "PUBLIC_BASE_URL=$url"
    Set-Content .env $text -NoNewline
    docker compose up -d api | Out-Null
    Write-Host "Public link: $url  (written to PUBLIC_BASE_URL; api restarted so case links use it)"
}

switch ($Target) {
    "help" {
        Get-Content $PSCommandPath | Select-String -Pattern '^\s+"([a-z-]+)" \{ # (.*)$' | ForEach-Object {
            "{0,-14} {1}" -f $_.Matches.Groups[1].Value, $_.Matches.Groups[2].Value
        }
    }
    "setup" { # Create .env with generated secrets and the DATA_ROOT folders
        Invoke-Setup }
    "venv" { # -Local only: create .venv with the backend requirements
        python -m venv .venv; .\.venv\Scripts\pip install -r backend\requirements.txt }
    "build" { # Build the containers
        docker compose build }
    "up" { # Start the lite profile on http://localhost:8080
        docker compose up -d }
    "down" { # Stop everything (data is kept)
        docker compose down }
    "logs" { # Follow the API logs
        docker compose logs -f --tail=100 api }
    "migrate" { # Create or update schema, roles and row-level security
        Invoke-Py @("-m", "voltguard", "migrate") }
    "seed" { # Demo accounts, simulation, closed cases, RAG documents
        Invoke-Py @("-m", "voltguard", "seed") }
    "simulate" { # Simulate the demo zones
        Invoke-Py @("-m", "voltguard", "simulate", "--run", "demo") }
    "train" { # Train the pattern model and the autoencoder
        Invoke-Py @("-m", "voltguard", "train-models") }
    "tune" { # Tune weights on the tuning split only
        Invoke-Py @("-m", "voltguard", "tune") }
    "simreport" { # Write reports/simulation_report.md
        Invoke-Py @("-m", "voltguard", "simreport") }
    "pipeline" { # Load the active sources and run detection (no cases)
        Invoke-Py @("-m", "voltguard", "pipeline") }
    "ingest" { # Validate and load an uploaded dataset: -Dataset <name>
        if (-not $Dataset) { throw "usage: .\make.ps1 ingest -Dataset <dataset_name>" }
        Invoke-Py @("-m", "voltguard", "ingest", $Dataset) }
    "fetch" { # Try to download the public datasets (prints manual steps on failure)
        Invoke-Py @("/app/scripts/fetch_datasets.py") }
    "models" { # Pull the language and embedding models onto D:
        $model = ((Get-Content .env | Where-Object { $_ -match "^LLM_MODEL=" }) -replace "^LLM_MODEL=", "" -replace "\s+#.*$", "").Trim()
        docker compose exec ollama ollama pull $model
        Invoke-Py @("-m", "voltguard", "fetch-models") }
    "test" { # Run the test suite
        Invoke-Py @("-m", "pytest") }
    "demo" { # Fresh setup, seed, detection run and the printed demo script
        Invoke-Setup
        docker compose up -d --build
        Invoke-Py @("-m", "voltguard", "migrate")
        Invoke-Py @("-m", "voltguard", "demo") }
    "tunnel" { # Quick Cloudflare tunnel; writes PUBLIC_BASE_URL
        Invoke-Tunnel "quick" }
    "tunnel-named" { # Named Cloudflare tunnel with a stable hostname
        Invoke-Tunnel "named" }
    "snapshot" { # Export rpt_ views to CSV for Power BI
        Invoke-Py @("-m", "voltguard", "snapshot") }
    "backtest" { # Day-by-day back-test on simulated history
        Invoke-Py @("/app/scripts/backtest.py") }
    "handoff" { # Rebuild the graphify graph and HANDOFF.md (needs Git Bash or WSL)
        bash scripts/handoff.sh }
    default { throw "Unknown target '$Target'. Run .\make.ps1 help" }
}
