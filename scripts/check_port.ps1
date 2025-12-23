# PowerShell script to check what's using a port

param(
    [int]$Port = 8080
)

Write-Host "Checking what's using port $Port..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if ($connections) {
    Write-Host "`nPort $Port is in use by:" -ForegroundColor Yellow
    
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "`nProcess ID: $($conn.OwningProcess)" -ForegroundColor White
        Write-Host "Process Name: $($process.ProcessName)" -ForegroundColor White
        Write-Host "State: $($conn.State)" -ForegroundColor White
        Write-Host "Local Address: $($conn.LocalAddress):$($conn.LocalPort)" -ForegroundColor White
        
        if ($process) {
            Write-Host "Full Path: $($process.Path)" -ForegroundColor Gray
        }
    }
    
    Write-Host "`nTo stop a process:" -ForegroundColor Yellow
    Write-Host "  Stop-Process -Id <ProcessID> -Force" -ForegroundColor White
    Write-Host "`nOr to stop all processes using this port:" -ForegroundColor Yellow
    Write-Host "  Get-NetTCPConnection -LocalPort $Port | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force }" -ForegroundColor White
} else {
    Write-Host "✅ Port $Port is available" -ForegroundColor Green
}

