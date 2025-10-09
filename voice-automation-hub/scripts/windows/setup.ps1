# Voice Automation Hub - Windows Setup Script
# Run as Administrator

Write-Host "🚀 Voice Automation Hub - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Check Python installation
Write-Host "📦 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# Check Node.js installation
Write-Host "`n📦 Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found! Please install Node.js 18+ from nodejs.org" -ForegroundColor Red
    exit 1
}

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Set-Location $projectRoot

Write-Host "`n📂 Project root: $projectRoot" -ForegroundColor Cyan

# Setup Backend
Write-Host "`n🐍 Setting up Python backend..." -ForegroundColor Yellow
Set-Location "$projectRoot\backend"

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping creation" -ForegroundColor Gray
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Gray
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
Write-Host "Installing Playwright browsers..." -ForegroundColor Gray
playwright install chromium

Write-Host "✅ Backend setup complete!" -ForegroundColor Green

# Setup Frontend
Write-Host "`n⚛️  Setting up Next.js frontend..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend"

# Install Node dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Gray
npm install

Write-Host "✅ Frontend setup complete!" -ForegroundColor Green

# Setup Environment
Write-Host "`n🔐 Setting up environment variables..." -ForegroundColor Yellow
Set-Location $projectRoot

if (Test-Path ".env") {
    Write-Host ".env file already exists, skipping..." -ForegroundColor Gray
} else {
    Write-Host "Copying .env.example to .env..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env and add your API keys!" -ForegroundColor Yellow
}

# Create MCP servers directory
Write-Host "`n📁 Creating MCP servers directory..." -ForegroundColor Yellow
$mcpPath = "$projectRoot\backend\mcp_servers"
if (-not (Test-Path $mcpPath)) {
    New-Item -ItemType Directory -Path $mcpPath -Force | Out-Null
    Write-Host "✅ Created: $mcpPath" -ForegroundColor Green
}

# Create logs directory
Write-Host "📁 Creating logs directory..." -ForegroundColor Yellow
$logsPath = "$projectRoot\logs"
if (-not (Test-Path $logsPath)) {
    New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
    Write-Host "✅ Created: $logsPath" -ForegroundColor Green
}

# Create startup scripts
Write-Host "`n📝 Creating startup scripts..." -ForegroundColor Yellow

# Create start.bat
$startBat = @"
@echo off
echo Starting Voice Automation Hub...
echo.

start "Backend" cmd /k "cd /d %~dp0..\backend && venv\Scripts\activate && python server.py"
timeout /t 3 /nobreak > nul

start "Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo ======================================
echo Voice Automation Hub is starting!
echo ======================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to open browser...
pause > nul

start http://localhost:3000
"@

$startBat | Out-File -FilePath "$projectRoot\scripts\windows\start.bat" -Encoding ASCII

# Create stop.bat
$stopBat = @"
@echo off
echo Stopping Voice Automation Hub...

taskkill /FI "WINDOWTITLE eq Backend*" /F 2>nul
taskkill /FI "WINDOWTITLE eq Frontend*" /F 2>nul

echo.
echo ✅ Voice Automation Hub stopped!
pause
"@

$stopBat | Out-File -FilePath "$projectRoot\scripts\windows\stop.bat" -Encoding ASCII

Write-Host "✅ Startup scripts created!" -ForegroundColor Green

# Summary
Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file and add your OpenAI API key" -ForegroundColor White
Write-Host "2. Run: .\scripts\windows\start.bat" -ForegroundColor White
Write-Host "3. Open: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host "  Start:  .\scripts\windows\start.bat" -ForegroundColor White
Write-Host "  Stop:   .\scripts\windows\stop.bat" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: README.md" -ForegroundColor Yellow
Write-Host "Support: https://github.com/Zeeeepa/codegen/issues" -ForegroundColor Gray
Write-Host ""

