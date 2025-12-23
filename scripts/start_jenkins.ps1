# PowerShell script to start Jenkins in Docker

Write-Host "Starting Jenkins in Docker..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if port 8080 is in use
$port8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($port8080) {
    Write-Host "⚠️  Port 8080 is already in use" -ForegroundColor Yellow
    Write-Host "Checking if Jenkins container exists..." -ForegroundColor Cyan
}

# Check if Jenkins container already exists
$existingContainer = docker ps -a --filter "name=jenkins" --format "{{.Names}}" 2>$null
if ($existingContainer -eq "jenkins") {
    Write-Host "Jenkins container already exists. Checking status..." -ForegroundColor Yellow
    
    $running = docker ps --filter "name=jenkins" --format "{{.Names}}" 2>$null
    if ($running -eq "jenkins") {
        Write-Host "✅ Jenkins is already running" -ForegroundColor Green
        Write-Host "Access Jenkins at: http://localhost:8080" -ForegroundColor Cyan
        
        # Get initial password
        Write-Host "`nGetting initial admin password..." -ForegroundColor Cyan
        $password = docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>$null
        if ($password) {
            Write-Host "Initial admin password: $password" -ForegroundColor Yellow
        }
        exit 0
    } else {
        Write-Host "Starting existing Jenkins container..." -ForegroundColor Yellow
        docker start jenkins 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Host "✅ Jenkins started" -ForegroundColor Green
    }
} elseif ($port8080) {
    Write-Host "❌ Port 8080 is in use but no Jenkins container found." -ForegroundColor Red
    Write-Host "Please stop the service using port 8080 or use a different port." -ForegroundColor Yellow
    Write-Host "To use a different port, modify the script or run:" -ForegroundColor Yellow
    Write-Host "  docker run -d --name jenkins -p 8081:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts" -ForegroundColor White
    exit 1
} else {
    # Create and start new Jenkins container
    Write-Host "Creating new Jenkins container..." -ForegroundColor Cyan
    
    # Build Docker command arguments
    $dockerArgs = @(
        "run", "-d",
        "--name", "jenkins",
        "-p", "8080:8080",
        "-p", "50000:50000",
        "-v", "jenkins_home:/var/jenkins_home"
    )
    
    # Add Docker socket mount for Linux/Mac (not needed on Windows)
    if (-not ($IsWindows -or $env:OS -like "*Windows*")) {
        $dockerArgs += @("-v", "/var/run/docker.sock:/var/run/docker.sock")
    }
    
    $dockerArgs += "jenkins/jenkins:lts"
    
    # Run Docker command
    & docker $dockerArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Jenkins container created and started" -ForegroundColor Green
        Write-Host "Waiting for Jenkins to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        Write-Host "❌ Failed to start Jenkins container" -ForegroundColor Red
        exit 1
    }
}

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
    Write-Host "http://localhost:8080" -ForegroundColor Cyan
    Write-Host "Initial Admin Password: " -NoNewline -ForegroundColor White
    Write-Host $password.Trim() -ForegroundColor Yellow
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Open http://localhost:8080 in your browser" -ForegroundColor White
    Write-Host "2. Enter the password above" -ForegroundColor White
    Write-Host "3. Install recommended plugins" -ForegroundColor White
    Write-Host "4. Create admin user" -ForegroundColor White
} else {
    Write-Host "⚠️  Could not retrieve initial password. Check container logs:" -ForegroundColor Yellow
    Write-Host "   docker logs jenkins" -ForegroundColor White
    Write-Host "`nAccess Jenkins at: http://localhost:8080" -ForegroundColor Cyan
}

# Show container status
Write-Host "`nContainer status:" -ForegroundColor Cyan
docker ps --filter "name=jenkins" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

