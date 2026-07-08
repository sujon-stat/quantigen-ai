# =====================================================================
# StatMind AI — Universal One-Click Production Launcher (Windows)
# =====================================================================

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "         StatMind AI — Universal Production Launcher" -ForegroundColor White
Write-Host "=====================================================================`n" -ForegroundColor Cyan

# 1. Ensure Node.js is in PATH for building frontend
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH

# 2. Build Production Single Page Application if needed
Write-Host "[1/2] Compiling Production Frontend (React 18 + Vite)..." -ForegroundColor Yellow
Set-Location -Path "$PSScriptRoot\frontend"
& "C:\Program Files\nodejs\npm.cmd" run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error compiling frontend! Please ensure Node.js is installed." -ForegroundColor Red
    exit 1
}
Set-Location -Path "$PSScriptRoot"

# 3. Detect Local Network IPv4 Address for universal LAN sharing
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
if (-not $lanIp) { $lanIp = "127.0.0.1" }

# 4. Launch Unified Production Server hosting BOTH REST API and React SPA on port 8000
Write-Host "`n[2/2] Launching StatMind AI Unified Server on port 8000..." -ForegroundColor Green
Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  -> Local Access:   " -NoNewline -ForegroundColor Gray; Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "  -> Network Access: " -NoNewline -ForegroundColor Gray; Write-Host "http://${lanIp}:8000" -ForegroundColor Cyan
Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "StatMind AI is now running universally! Press Ctrl+C to stop.`n" -ForegroundColor Yellow

# Automatically launch browser after 2 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"
} | Out-Null

# Start FastAPI/Uvicorn server bound to 0.0.0.0
& uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
