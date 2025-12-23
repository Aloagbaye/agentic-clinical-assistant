# PowerShell script to manage Jenkins containers

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("list", "stop", "start", "remove", "status", "logs", "password")]
    [string]$Action = "status",
    
    [int]$Port = 8080
)

Write-Host "Jenkins Container Management" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

switch ($Action) {
    "list" {
        Write-Host "`nAll Jenkins containers:" -ForegroundColor Yellow
        docker ps -a --filter "name=jenkins" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
    }
    
    "status" {
        Write-Host "`nRunning Jenkins containers:" -ForegroundColor Yellow
        $running = docker ps --filter "name=jenkins" --format "{{.Names}}"
        if ($running) {
            docker ps --filter "name=jenkins" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
            
            Write-Host "`nPort usage:" -ForegroundColor Yellow
            $ports = @(8080, 8081, 8082, 8083, 8084, 8085)
            foreach ($p in $ports) {
                $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
                if ($conn) {
                    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                    Write-Host "  Port $p : " -NoNewline -ForegroundColor White
                    Write-Host "IN USE by $($proc.ProcessName) (PID: $($conn.OwningProcess))" -ForegroundColor Red
                } else {
                    Write-Host "  Port $p : " -NoNewline -ForegroundColor White
                    Write-Host "AVAILABLE" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "No Jenkins containers are running" -ForegroundColor Yellow
        }
    }
    
    "stop" {
        Write-Host "`nStopping Jenkins container..." -ForegroundColor Yellow
        docker stop jenkins
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Jenkins stopped" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to stop Jenkins" -ForegroundColor Red
        }
    }
    
    "start" {
        Write-Host "`nStarting Jenkins container..." -ForegroundColor Yellow
        docker start jenkins
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Jenkins started" -ForegroundColor Green
            Start-Sleep -Seconds 3
            docker ps --filter "name=jenkins" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        } else {
            Write-Host "❌ Failed to start Jenkins" -ForegroundColor Red
        }
    }
    
    "remove" {
        Write-Host "`n⚠️  This will remove the Jenkins container and all its data!" -ForegroundColor Red
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            docker stop jenkins 2>&1 | Out-Null
            docker rm jenkins
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Jenkins container removed" -ForegroundColor Green
            } else {
                Write-Host "❌ Failed to remove Jenkins" -ForegroundColor Red
            }
        } else {
            Write-Host "Cancelled" -ForegroundColor Yellow
        }
    }
    
    "logs" {
        Write-Host "`nJenkins container logs (last 50 lines):" -ForegroundColor Yellow
        docker logs jenkins --tail 50
    }
    
    "password" {
        Write-Host "`nGetting Jenkins initial admin password..." -ForegroundColor Yellow
        $password = docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>$null
        if ($password) {
            Write-Host "Initial Admin Password: " -NoNewline -ForegroundColor White
            Write-Host $password.Trim() -ForegroundColor Yellow
        } else {
            Write-Host "❌ Could not retrieve password. Container may not be running." -ForegroundColor Red
        }
    }
}

Write-Host "`n" -NoNewline

