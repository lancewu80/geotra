<#
Copy the whole `peoplecount` folder to the new machine, then run:

    powershell -ExecutionPolicy Bypass -File start.ps1

(Double-clicking may get blocked by Windows' default script execution
policy -- if so, use the command above from a terminal instead.)

One-time OS-level installs still required on the new machine (nothing to
do with this project, so they can't be scripted around): Docker Desktop,
Python 3.11, Node.js 20+, an NVIDIA driver. Everything else -- venv
creation, GPU PyTorch install, npm install, .env creation, demo data,
starting every service -- is handled here, and it's safe to re-run (it
skips steps that are already done and won't double-launch services).

The backend runs natively (NOT in a Docker container) specifically so it
can read the laptop's built-in webcam directly. Docker Desktop on Windows
can't reach physical camera devices without extra WSL2/usbipd setup;
keeping the YOLO process outside Docker sidesteps that entirely. Only
Postgres runs in Docker, since a database doesn't need camera access.
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

function Test-PortOpen($port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("localhost", $port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

Write-Host "==> Starting Postgres (Docker)..."
Push-Location $backend
docker compose up -d
for ($i = 0; $i -lt 30; $i++) {
    docker compose exec -T postgres pg_isready -U peoplecount *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 2
}
Pop-Location

if (-not (Test-Path (Join-Path $backend ".env"))) {
    Write-Host "==> Creating backend/.env from defaults"
    Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
}

if (-not (Test-Path $venvPython)) {
    Write-Host "==> First run: creating backend venv + installing GPU PyTorch (this takes a while)"
    python -m venv (Join-Path $backend ".venv")
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    & $venvPython -m pip install -r (Join-Path $backend "requirements.txt")
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "==> First run: npm install"
    Push-Location $frontend
    npm install
    Pop-Location
}

if (-not (Test-PortOpen 8000)) {
    Write-Host "==> Starting backend on :8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$backend`"; & `"$venvPython`" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
} else {
    Write-Host "==> Backend already running on :8000"
}

Write-Host "==> Waiting for backend to come up..."
for ($i = 0; $i -lt 30; $i++) {
    if (Test-PortOpen 8000) { break }
    Start-Sleep -Seconds 1
}

Write-Host "==> Seeding demo zone/line (safe to re-run, skips if already seeded)"
& $venvPython (Join-Path $backend "scripts\seed_demo.py")

if (-not (Test-PortOpen 5173)) {
    Write-Host "==> Starting frontend on :5173"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$frontend`"; npm run dev"
} else {
    Write-Host "==> Frontend already running on :5173"
}

Write-Host "==> Waiting for frontend to come up..."
for ($i = 0; $i -lt 30; $i++) {
    if (Test-PortOpen 5173) { break }
    Start-Sleep -Seconds 1
}

Start-Process "http://localhost:5173"
Write-Host "==> Done. Dashboard: http://localhost:5173 (backend/frontend logs are in the two new windows)"
