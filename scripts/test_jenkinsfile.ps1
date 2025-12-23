# PowerShell script to test Jenkinsfile locally

Write-Host "Testing Jenkinsfile..." -ForegroundColor Cyan

# Check if Jenkins is accessible
$jenkinsUrl = "http://localhost:8080"
try {
    $response = Invoke-WebRequest -Uri "$jenkinsUrl/login" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Jenkins is accessible at $jenkinsUrl" -ForegroundColor Green
} catch {
    Write-Host "❌ Jenkins is not accessible at $jenkinsUrl" -ForegroundColor Red
    Write-Host "Please start Jenkins first" -ForegroundColor Yellow
    exit 1
}

# Download jenkins-cli.jar if not present
$cliJar = "jenkins-cli.jar"
if (-not (Test-Path $cliJar)) {
    Write-Host "Downloading jenkins-cli.jar..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "$jenkinsUrl/jnlpJars/jenkins-cli.jar" -OutFile $cliJar
        Write-Host "✅ Downloaded jenkins-cli.jar" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download jenkins-cli.jar" -ForegroundColor Red
        exit 1
    }
}

# Get Jenkins admin password
$passwordFile = "$env:USERPROFILE\.jenkins\secrets\initialAdminPassword"
if (-not (Test-Path $passwordFile)) {
    Write-Host "❌ Jenkins admin password file not found" -ForegroundColor Red
    Write-Host "Please check Jenkins installation" -ForegroundColor Yellow
    exit 1
}

$adminPassword = Get-Content $passwordFile -Raw | ForEach-Object { $_.Trim() }

# Validate Jenkinsfile syntax
Write-Host "Validating Jenkinsfile syntax..." -ForegroundColor Cyan
$jenkinsfileContent = Get-Content "Jenkinsfile" -Raw

try {
    $result = java -jar $cliJar -s $jenkinsUrl -auth "admin:$adminPassword" declarative-linter @jenkinsfileContent
    Write-Host "✅ Jenkinsfile syntax is valid" -ForegroundColor Green
} catch {
    Write-Host "❌ Jenkinsfile validation failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "To test stages individually:" -ForegroundColor Yellow
Write-Host "1. Open Jenkins Blue Ocean UI at $jenkinsUrl/blue" -ForegroundColor White
Write-Host "2. Create a new pipeline from Jenkinsfile" -ForegroundColor White
Write-Host "3. Run individual stages" -ForegroundColor White

