# Quick Start: Jenkins for Testing

Quick guide to start Jenkins locally for testing the Jenkinsfile.

## Windows (PowerShell)

### Option 1: Use the Script (Recommended)

```powershell
powershell scripts/start_jenkins.ps1
```

This script will:
- Check if Docker is running
- Check if Jenkins container already exists
- Create and start Jenkins if needed
- Display the initial admin password
- Show Jenkins URL

### Option 2: Manual Start

```powershell
docker run -d `
  --name jenkins `
  -p 8080:8080 `
  -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  jenkins/jenkins:lts
```

### Get Initial Password

```powershell
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

## Linux/Mac (Bash)

### Option 1: Use Docker

```bash
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

### Get Initial Password

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

## Access Jenkins

1. **Open Browser**: http://localhost:8080
2. **Enter Password**: Use the password from above
3. **Install Plugins**: Choose "Install suggested plugins"
4. **Create Admin**: Set up your admin account

## Create Pipeline Job

1. **New Item**: Click "New Item"
2. **Pipeline**: Select "Pipeline" and click OK
3. **Configure**:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL
   - **Script Path**: `Jenkinsfile`
4. **Save**: Click Save
5. **Build**: Click "Build Now"

## Troubleshooting

### Port Already in Use

If port 8080 is already in use:

```powershell
# Check what's using the port
netstat -ano | findstr :8080

# Stop existing Jenkins container
docker stop jenkins
docker rm jenkins

# Or use a different port
docker run -d --name jenkins -p 8081:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
```

### Container Already Exists

```powershell
# Remove existing container
docker rm -f jenkins

# Start fresh
powershell scripts/start_jenkins.ps1
```

### Docker Not Running

Make sure Docker Desktop is running on Windows, or Docker daemon is running on Linux/Mac.

## Next Steps

After Jenkins is running:

1. **Install Required Plugins**:
   - Docker Pipeline
   - Kubernetes
   - Git
   - Credentials Binding

2. **Configure Credentials** (if needed):
   - Docker registry credentials
   - Kubernetes config
   - Git credentials

3. **Test Jenkinsfile**:
   - Create pipeline job
   - Run build
   - Check console output

## Stop Jenkins

```powershell
# Stop container
docker stop jenkins

# Remove container (keeps data)
docker rm jenkins

# Remove container and data
docker rm -f jenkins
docker volume rm jenkins_home
```

