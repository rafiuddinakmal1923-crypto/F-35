<#
.SYNOPSIS
  VoltGuard AI R0 tasks for Windows (same targets as the Makefile).

.EXAMPLE
  .\make.ps1 demo
  .\make.ps1 ingest -Dataset tnb_extract_2026_10
  .\make.ps1 test -Local          # run with .\.venv instead of the api container
  .\make.ps1 tunnel -New          # replace a broken quick tunnel with a fresh address
#>
param(
    [Parameter(Position = 0)][string]$Target = "help",
    [string]$Dataset = "",
    [switch]$Local,
    [switch]$New
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
    if ($text -match "(?m)^DEMO_PASSWORDS=\s*(#.*)?$") {
        $users = (Select-String -Path config\demo.yaml -Pattern "user_id:\s*([\w.]+)" -AllMatches).Matches | ForEach-Object { $_.Groups[1].Value }
        $users += "pipeline"
        $pairs = ($users | ForEach-Object { "$_=$((New-Secret).Substring(0, 20))" }) -join ","
        $text = $text -replace "(?m)^DEMO_PASSWORDS=.*$", "DEMO_PASSWORDS=$pairs"
        Write-Host "Generated passwords for $($users.Count) test accounts (DEMO_PASSWORDS)"
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

# Open the public link from this laptop the way a visitor would, and say plainly why it fails if it does.
function Test-PublicLink([string]$Url) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $hostName = ([Uri]$Url).Host
    Write-Host "Checking that $Url answers from the internet (up to 90 s; new addresses take a moment)..."
    foreach ($i in 1..45) {
        try {
            $r = Invoke-WebRequest -Uri "$Url/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { Write-Host "OK: the public link works." -ForegroundColor Green; return $true }
        } catch { }
        Start-Sleep -Seconds 2
    }
    $public = $null
    try { $public = Resolve-DnsName $hostName -Server 1.1.1.1 -ErrorAction Stop } catch { }
    $local = $null
    try { $local = Resolve-DnsName $hostName -ErrorAction Stop } catch { }
    if (-not $public) {
        Write-Warning "The address $hostName does not exist on the internet: the tunnel is not connected. See: docker compose --profile tunnel logs --tail 30 tunnel. Then try: .\make.ps1 tunnel -New"
    } elseif (-not $local) {
        Write-Warning "The internet knows $hostName, but this laptop's network does not (DNS cache, router or antivirus web protection). Try: ipconfig /flushdns, wait a minute, use a phone on mobile data, or set the laptop's DNS to 1.1.1.1."
    } else {
        Write-Warning "$hostName resolves but the app did not answer through it. Check: docker compose ps (proxy, api and web running) and docker compose --profile tunnel logs --tail 30 tunnel."
    }
    return $false
}

# A quick tunnel gets a new address whenever it restarts: keep PUBLIC_BASE_URL in .env pointing at
# the live one (or clear it when no tunnel runs), so printed and messaged links are never stale.
function Sync-QuickTunnelUrl {
    $text = Get-Content .env -Raw
    if ($text -notmatch "(?m)^PUBLIC_BASE_URL=https://[a-z0-9-]+\.trycloudflare\.com") { return }
    $running = docker compose ps --status running --services 2>$null | Where-Object { $_.Trim() -eq "tunnel" }
    $url = ""
    if ($running) {
        $url = (docker compose --profile tunnel logs tunnel 2>&1 | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches |
                ForEach-Object { $_.Matches.Value } | Select-Object -Last 1)
    }
    if (-not $url) { Write-Warning "The quick tunnel is not running, so the public link in .env is cleared. Start one with: .\make.ps1 tunnel" }
    $updated = $text -replace "(?m)^PUBLIC_BASE_URL=.*$", "PUBLIC_BASE_URL=$url"
    if ($updated -ne $text) {
        Set-Content .env $updated -NoNewline
        docker compose up -d api | Out-Null      # case links in messages follow the live address
    }
}

function Invoke-Tunnel([string]$Mode) {
    if ($Mode -eq "quick") {
        $running = docker compose ps --status running --services 2>$null | Where-Object { $_.Trim() -eq "tunnel" }
        if ($running -and $New) {
            Write-Warning "Replacing the running quick tunnel: the old address, saved phone sign-ins and links already sent stop working."
            docker compose --profile tunnel rm -sf tunnel | Out-Null
            $running = $null
        }
        if ($running) {
            Write-Warning "A quick tunnel is already running; keeping its address (restarting would break saved phone sign-ins and links already sent). If the link is broken, run: .\make.ps1 tunnel -New"
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
        # Quick tunnels print a new address each time cloudflared starts: wait until this one is registered.
        foreach ($i in 1..20) {
            if (docker compose --profile tunnel logs tunnel 2>&1 | Select-String -SimpleMatch "Registered tunnel connection") { break }
            Start-Sleep -Seconds 2
        }
    } elseif ($Mode -eq "token") {
        $token = ((Get-Content .env | Where-Object { $_ -match "^TUNNEL_TOKEN=" }) -replace "^TUNNEL_TOKEN=", "" -replace "\s+#.*$", "").Trim()
        if (-not $token) { throw "Set TUNNEL_TOKEN in .env first (Cloudflare dashboard -> Zero Trust -> Networks -> Tunnels; see HOW_TO_RUN.md)." }
        docker compose --profile tunnel-token up -d tunnel-token
        $hostLine = (Get-Content .env | Where-Object { $_ -match "^TUNNEL_HOSTNAME=" }) -replace "^TUNNEL_HOSTNAME=", "" -replace "\s+#.*$", ""
        if (-not $hostLine.Trim()) { throw "Set TUNNEL_HOSTNAME in .env to the public hostname you gave the tunnel." }
        $url = "https://$($hostLine.Trim())"
    } else {
        if (-not (Test-Path deploy\cloudflared\config.yml)) { throw "Copy deploy\cloudflared\config.example.yml to config.yml and fill it in first." }
        docker compose --profile tunnel-named up -d tunnel-named
        $hostLine = (Get-Content .env | Where-Object { $_ -match "^TUNNEL_HOSTNAME=" }) -replace "^TUNNEL_HOSTNAME=", "" -replace "\s+#.*$", ""
        $url = "https://$($hostLine.Trim())"
    }
    $text = Get-Content .env -Raw
    $text = $text -replace "(?m)^PUBLIC_BASE_URL=.*$", "PUBLIC_BASE_URL=$url"
    Set-Content .env $text -NoNewline
    docker compose up -d api | Out-Null
    Write-Host "Public link: $url  (written to PUBLIC_BASE_URL; api restarted so case links use it)"
    Write-Host "Phone (inspector app): $url/#/field"
    Test-PublicLink $url | Out-Null
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
    "up" { # Start the lite profile on http://localhost:8080 (WEB_PORT in .env)
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
        Sync-QuickTunnelUrl
        Invoke-Py @("-m", "voltguard", "demo") }
    "tunnel" { # Quick Cloudflare tunnel; writes PUBLIC_BASE_URL (-New replaces a broken one)
        Invoke-Tunnel "quick" }
    "tunnel-named" { # Named Cloudflare tunnel with a stable hostname
        Invoke-Tunnel "named" }
    "tunnel-token" { # Stable link from a Cloudflare dashboard tunnel (TUNNEL_TOKEN and TUNNEL_HOSTNAME in .env)
        Invoke-Tunnel "token" }
    "tunnel-stop" { # Stop every public link (the app keeps running on this laptop)
        docker compose --profile tunnel --profile tunnel-named --profile tunnel-token stop tunnel tunnel-named tunnel-token
        $text = Get-Content .env -Raw
        Set-Content .env ($text -replace "(?m)^PUBLIC_BASE_URL=.*$", "PUBLIC_BASE_URL=") -NoNewline
        docker compose up -d api | Out-Null
        Write-Host "Public links stopped; case links point at this laptop again." }
    "snapshot" { # Export rpt_ views to CSV for Power BI
        Invoke-Py @("-m", "voltguard", "snapshot") }
    "backtest" { # Day-by-day back-test on simulated history
        Invoke-Py @("/app/scripts/backtest.py") }
    "handoff" { # Rebuild the graphify graph and HANDOFF.md (needs Git Bash or WSL)
        bash scripts/handoff.sh }
    default { throw "Unknown target '$Target'. Run .\make.ps1 help" }
}
