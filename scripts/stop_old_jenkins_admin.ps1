# Script to stop old Jenkins - Run as Administrator

Write-Host "Stopping old Jenkins instance on port 8080..." -ForegroundColor Cyan
Write-Host "⚠️  This script requires Administrator privileges" -ForegroundColor Yellow

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nTo run as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Navigate to project directory" -ForegroundColor White
    Write-Host "  4. Run: powershell scripts/stop_old_jenkins_admin.ps1" -ForegroundColor White
    exit 1
}

$connections = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue

if ($connections) {
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "`nFound process using port 8080:" -ForegroundColor Yellow
            Write-Host "  Process Name: $($process.ProcessName)" -ForegroundColor White
            Write-Host "  Process ID: $($conn.OwningProcess)" -ForegroundColor White
            
            if ($process.ProcessName -eq "java") {
                Write-Host "`nStopping Java process (likely old Jenkins)..." -ForegroundColor Yellow
                
                # Try Stop-Process first
                try {
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop
                    Start-Sleep -Seconds 2
                    
                    # Verify it's stopped
                    $check = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
                    if (-not $check) {
                        Write-Host "✅ Process stopped successfully. Port 8080 is now available." -ForegroundColor Green
                    } else {
                        Write-Host "⚠️  Process may still be running." -ForegroundColor Yellow
                    }
                } catch {
                    Write-Host "❌ Failed to stop process: $($_.Exception.Message)" -ForegroundColor Red
                    Write-Host "`nTrying taskkill command..." -ForegroundColor Yellow
                    
                    # Try taskkill as alternative
                    $result = taskkill /PID $conn.OwningProcess /F 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "✅ Process stopped using taskkill." -ForegroundColor Green
                    } else {
                        Write-Host "❌ Failed to stop process even with taskkill." -ForegroundColor Red
                        Write-Host "You may need to stop it manually via Task Manager." -ForegroundColor Yellow
                    }
                }
            } else {
                Write-Host "`n⚠️  This is not a Java process. Be careful stopping it." -ForegroundColor Red
                $confirm = Read-Host "Continue anyway? (yes/no)"
                if ($confirm -eq "yes") {
                    Stop-Process -Id $conn.OwningProcess -Force
                }
            }
        }
    }
} else {
    Write-Host "✅ Port 8080 is already available" -ForegroundColor Green
}

Write-Host "`nDone!" -ForegroundColor Cyan

