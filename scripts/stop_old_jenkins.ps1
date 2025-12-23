# Script to stop the old Jenkins instance on port 8080

Write-Host "Checking for old Jenkins instance on port 8080..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue

if ($connections) {
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "`nFound process using port 8080:" -ForegroundColor Yellow
            Write-Host "  Process Name: $($process.ProcessName)" -ForegroundColor White
            Write-Host "  Process ID: $($conn.OwningProcess)" -ForegroundColor White
            Write-Host "  Path: $($process.Path)" -ForegroundColor Gray
            
            if ($process.ProcessName -eq "java") {
                Write-Host "`n⚠️  This appears to be a Java application (likely old Jenkins)" -ForegroundColor Yellow
                $confirm = Read-Host "Do you want to stop this process? (yes/no)"
                
                if ($confirm -eq "yes") {
                    Write-Host "Stopping process..." -ForegroundColor Yellow
                    
                    # Try to stop with Stop-Process first
                    try {
                        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop
                        Start-Sleep -Seconds 2
                        
                        # Verify it's stopped
                        $check = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
                        if (-not $check) {
                            Write-Host "✅ Process stopped. Port 8080 is now available." -ForegroundColor Green
                            Write-Host "`nYou can now start Jenkins on port 8080 if desired:" -ForegroundColor Cyan
                            Write-Host "  powershell scripts/start_jenkins.ps1" -ForegroundColor White
                        } else {
                            Write-Host "⚠️  Process may still be running." -ForegroundColor Yellow
                        }
                    } catch {
                        Write-Host "❌ Access denied. Process requires administrator privileges." -ForegroundColor Red
                        Write-Host "`nTry one of these options:" -ForegroundColor Yellow
                        Write-Host "`nOption 1: Run PowerShell as Administrator" -ForegroundColor Cyan
                        Write-Host "  1. Right-click PowerShell" -ForegroundColor White
                        Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
                        Write-Host "  3. Run: powershell scripts/stop_old_jenkins.ps1" -ForegroundColor White
                        
                        Write-Host "`nOption 2: Use taskkill command (run as admin)" -ForegroundColor Cyan
                        Write-Host "  taskkill /PID $($conn.OwningProcess) /F" -ForegroundColor White
                        
                        Write-Host "`nOption 3: Use Task Manager" -ForegroundColor Cyan
                        Write-Host "  1. Open Task Manager (Ctrl+Shift+Esc)" -ForegroundColor White
                        Write-Host "  2. Find process ID $($conn.OwningProcess)" -ForegroundColor White
                        Write-Host "  3. Right-click → End Task" -ForegroundColor White
                        
                        Write-Host "`nOption 4: Just use port 8083 (recommended)" -ForegroundColor Cyan
                        Write-Host "  The new Jenkins is already running on port 8083" -ForegroundColor White
                        Write-Host "  Access it at: http://localhost:8083" -ForegroundColor White
                        Write-Host "  No need to stop the old Jenkins!" -ForegroundColor Green
                    }
                } else {
                    Write-Host "Process not stopped." -ForegroundColor Yellow
                }
            } else {
                Write-Host "`n⚠️  This is not a Java process. Be careful stopping it." -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "✅ Port 8080 is available" -ForegroundColor Green
}

