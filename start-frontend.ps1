# TechBank.ai Frontend Startup Script
# This script starts the frontend development server

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║    🎨 Starting TechBank.ai Frontend Server 🎨     ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Change to frontend directory
$frontendDir = Join-Path $PSScriptRoot "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $frontendDir

# Check if node_modules exists
$nodeModulesPath = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModulesPath)) {
    Write-Host "⚠️  Dependencies not installed. Installing..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# Check if backend is running
Write-Host "`n🔍 Checking backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend is not running on http://localhost:8000" -ForegroundColor Yellow
    Write-Host "   Frontend will still start, but API calls will fail." -ForegroundColor Yellow
    Write-Host "   Start backend with: .\start-backend.ps1" -ForegroundColor Cyan
}

# Start the frontend server
Write-Host "`n🚀 Starting frontend development server..." -ForegroundColor Green
Write-Host "   Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   (If port 3000 is busy, Vite will use 3001)" -ForegroundColor Cyan
Write-Host "`n   Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

npm run dev

