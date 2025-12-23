# PowerShell script to start Jenkins on an alternative port

param(
    [int]$Port = 8081
)

Write-Host "Starting Jenkins on port $Port..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if port is available
$portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "❌ Port $Port is already in use. Please choose a different port." -ForegroundColor Red
    exit 1
}

# Check if Jenkins container already exists
$existingContainer = docker ps -a --filter "name=jenkins" --format "{{.Names}}" 2>$null
if ($existingContainer -eq "jenkins") {
    Write-Host "⚠️  Jenkins container already exists with name 'jenkins'" -ForegroundColor Yellow
    Write-Host "Removing existing container..." -ForegroundColor Yellow
    docker rm -f jenkins 2>&1 | Out-Null
}

# Create and start new Jenkins container on alternative port
Write-Host "Creating Jenkins container on port $Port..." -ForegroundColor Cyan

$dockerArgs = @(
    "run", "-d",
    "--name", "jenkins",
    "-p", "$Port`:8080",
    "-p", "50000:50000",
    "-v", "jenkins_home:/var/jenkins_home"
)

$dockerArgs += "jenkins/jenkins:lts"

# Run Docker command
$result = & docker $dockerArgs 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Jenkins container created and started" -ForegroundColor Green
    Write-Host "Waiting for Jenkins to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Get initial password
    Write-Host "`nGetting initial admin password..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    $maxRetries = 10
    $retryCount = 0
    $password = $null
    
    while ($retryCount -lt $maxRetries -and -not $password) {
        $password = docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>$null
        if (-not $password) {
            Start-Sleep -Seconds 2
            $retryCount++
        }
    }
    
    if ($password) {
        Write-Host ""
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host "Jenkins is ready!" -ForegroundColor Green
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host "URL: " -NoNewline -ForegroundColor White
        Write-Host "http://localhost:$Port" -ForegroundColor Cyan
        Write-Host "Initial Admin Password: " -NoNewline -ForegroundColor White
        Write-Host $password.Trim() -ForegroundColor Yellow
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host "`nNote: Jenkins is running on port $Port instead of 8080" -ForegroundColor Yellow
        Write-Host "`nNext steps:" -ForegroundColor Yellow
        Write-Host "1. Open http://localhost:$Port in your browser" -ForegroundColor White
        Write-Host "2. Enter the password above" -ForegroundColor White
        Write-Host "3. Install recommended plugins" -ForegroundColor White
        Write-Host "4. Create admin user" -ForegroundColor White
    } else {
        Write-Host "⚠️  Could not retrieve initial password. Check container logs:" -ForegroundColor Yellow
        Write-Host "   docker logs jenkins" -ForegroundColor White
        Write-Host "`nAccess Jenkins at: http://localhost:$Port" -ForegroundColor Cyan
    }
    
    # Show container status
    Write-Host "`nContainer status:" -ForegroundColor Cyan
    docker ps --filter "name=jenkins" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
} else {
    Write-Host "❌ Failed to start Jenkins container" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    exit 1
}

