# Jenkins Access Guide

## Current Situation

You have **TWO Jenkins instances** running:

### 1. Old Jenkins (Java Process)
- **Port**: 8080
- **Process**: Java (PID: 6664)
- **Password**: Your old Jenkins password
- **URL**: http://localhost:8080

### 2. New Jenkins (Docker Container)
- **Port**: 8083
- **Container**: `jenkins` (Docker)
- **Password**: `7e9b013128a74238929d3ede0b7a94aa`
- **URL**: http://localhost:8083

## Access the New Jenkins

**To access the NEW Jenkins (for testing your Jenkinsfile):**

1. Open: **http://localhost:8083** (NOT 8080)
2. Enter password: `7e9b013128a74238929d3ede0b7a94aa`
3. Complete setup wizard
4. Create pipeline job from your Jenkinsfile

## Stop Old Jenkins (Optional)

If you want to use port 8080 for the new Jenkins:

```powershell
# Check what's using port 8080
powershell scripts/check_port.ps1 -Port 8080

# Stop old Jenkins (if it's safe)
powershell scripts/stop_old_jenkins.ps1

# Then start new Jenkins on port 8080
powershell scripts/start_jenkins.ps1
```

## Manage Jenkins Containers

Use the management script:

```powershell
# Check status
powershell scripts/manage_jenkins.ps1 -Action status

# Get password
powershell scripts/manage_jenkins.ps1 -Action password

# View logs
powershell scripts/manage_jenkins.ps1 -Action logs

# Stop container
powershell scripts/manage_jenkins.ps1 -Action stop

# Start container
powershell scripts/manage_jenkins.ps1 -Action start
```

## Quick Reference

| Action | Command |
|--------|---------|
| Access NEW Jenkins | http://localhost:8083 |
| Access OLD Jenkins | http://localhost:8080 |
| Get NEW password | `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword` |
| Check status | `powershell scripts/manage_jenkins.ps1 -Action status` |
| Stop old Jenkins | `powershell scripts/stop_old_jenkins.ps1` |

## Important Notes

- **Port 8080** = Your old Jenkins (existing setup)
- **Port 8083** = New Jenkins (for testing Jenkinsfile)
- Both can run simultaneously
- Use port 8083 to test your new Jenkinsfile
- Keep port 8080 if you need your old Jenkins setup

