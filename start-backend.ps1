# TechBank.ai Backend Startup Script
# This script starts the backend server with proper setup

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 Starting TechBank.ai Backend Server 🚀      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Change to backend directory
$backendDir = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backendDir)) {
    Write-Host "❌ Backend directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir

# Check if virtual environment exists
$venvPath = Join-Path $backendDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n📦 Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
$envFile = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "`n⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env file with default values..." -ForegroundColor Yellow
    
    $envContent = @"
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=techbank
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Server Configuration
HOST=0.0.0.0
PORT=8000

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=10000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
"@
    
    Set-Content -Path $envFile -Value $envContent
    Write-Host "✅ .env file created. Please update with your credentials!" -ForegroundColor Green
}

# Check if dependencies are installed
Write-Host "`n🔍 Checking dependencies..." -ForegroundColor Yellow
$fastapiInstalled = python -c "import fastapi" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Dependencies not installed. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# Check if backend is already running
Write-Host "`n🔍 Checking if backend is already running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "⚠️  Backend is already running on http://localhost:8000" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop it first, or use a different port." -ForegroundColor Yellow
        exit 0
    }
} catch {
    # Backend is not running, which is what we want
}

# Start the backend server
Write-Host "`n🚀 Starting backend server..." -ForegroundColor Green
Write-Host "   Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "`n   Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

python -m src.main

