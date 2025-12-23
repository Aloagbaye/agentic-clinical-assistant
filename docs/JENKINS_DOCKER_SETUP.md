# Jenkins Docker Setup Guide

This guide explains how to set up Docker access for Jenkins so the pipeline can build and run Docker containers.

## Problem

The Jenkins pipeline needs Docker to:
- Run Python linting and tests in isolated containers
- Build Docker images for the API and worker services
- Run integration tests with docker-compose

If Docker is not available, you'll see errors like:
- `docker: not found`
- `docker: command not found`

## Solutions

### Option 1: Install Docker Pipeline Plugin (Recommended)

This is the easiest solution and doesn't require restarting Jenkins.

1. **Go to Jenkins**: http://localhost:8083
2. **Manage Jenkins** → **Plugins**
3. **Available** tab → Search: `Docker Pipeline`
4. **Install** (check the box, click "Install without restart")
5. **Restart Jenkins** when prompted

**Benefits**:
- No need to restart Jenkins container
- Better integration with Jenkins
- Handles Docker socket mounting automatically

### Option 2: Mount Docker Socket (For Docker-in-Docker)

If Jenkins is running in Docker, you need to mount the Docker socket so Jenkins can access the host's Docker daemon.

#### Stop Current Jenkins

```powershell
# Find Jenkins container
docker ps | Select-String "jenkins"

# Stop it (replace CONTAINER_ID with actual ID)
docker stop CONTAINER_ID
docker rm CONTAINER_ID
```

#### Start Jenkins with Docker Socket

**On Windows (Docker Desktop)**:
```powershell
docker run -d `
  --name jenkins `
  -p 8083:8080 `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  jenkins/jenkins:lts
```

**On Linux/Mac**:
```bash
docker run -d \
  --name jenkins \
  -p 8083:8080 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

**Note**: On Windows, Docker Desktop uses a named pipe, not a socket. You may need to use Docker Desktop's WSL2 backend or install Docker inside the Jenkins container.

#### Install Docker CLI in Jenkins Container

After starting Jenkins with socket mounted, install Docker CLI:

1. **Go to Jenkins**: http://localhost:8083
2. **Manage Jenkins** → **Tools** → **Global Tool Configuration**
3. **Docker** section → **Add Docker**
4. **Name**: `docker`
5. **Install automatically**: Check
6. **Version**: Latest
7. **Save**

Or install manually in the container:

```powershell
# Enter Jenkins container
docker exec -it jenkins bash

# Install Docker CLI
apt-get update
apt-get install -y docker.io

# Exit
exit
```

### Option 3: Use Docker-in-Docker (DinD)

This runs a Docker daemon inside the Jenkins container. **Not recommended** for production but works for testing.

```powershell
docker run -d `
  --name jenkins `
  -p 8083:8080 `
  -v jenkins_home:/var/jenkins_home `
  --privileged `
  jenkins/jenkins:lts
```

Then install Docker inside the container (see Option 2).

### Option 4: Skip Docker Stages (For Testing Only)

The updated Jenkinsfile will skip Docker-dependent stages if Docker is not available. This allows you to test the pipeline structure without Docker, but linting and tests won't run.

## Verify Docker Access

### Test from Jenkins UI

1. **Go to Jenkins**: http://localhost:8083
2. **New Item** → **Pipeline**
3. **Pipeline script**:
   ```groovy
   pipeline {
       agent any
       stages {
           stage('Test Docker') {
               steps {
                   script {
                       try {
                           docker.image('hello-world').inside {
                               sh 'echo "Docker works!"'
                           }
                       } catch (Exception e) {
                           sh 'docker run --rm hello-world'
                       }
                   }
               }
           }
       }
   }
   ```
4. **Build Now**
5. Check console output - should see "Hello from Docker!"

### Test from Command Line

```powershell
# Enter Jenkins container
docker exec -it jenkins bash

# Test Docker
docker --version
docker run --rm hello-world

# Exit
exit
```

## Troubleshooting

### Error: "docker: not found"

**Cause**: Docker CLI not installed in Jenkins container.

**Solution**:
1. Install Docker Pipeline plugin (Option 1), OR
2. Mount Docker socket and install Docker CLI (Option 2)

### Error: "Cannot connect to the Docker daemon"

**Cause**: Docker socket not mounted or permissions issue.

**Solution**:
1. Ensure Docker socket is mounted: `-v /var/run/docker.sock:/var/run/docker.sock`
2. On Linux, ensure Jenkins user is in `docker` group
3. On Windows, use Docker Desktop with WSL2 backend

### Error: "Permission denied" when accessing Docker socket

**Cause**: Jenkins user doesn't have permission to access Docker socket.

**Solution**:
```powershell
# Enter Jenkins container
docker exec -it jenkins bash

# Add jenkins user to docker group (if group exists)
usermod -aG docker jenkins

# Or change socket permissions (not recommended for production)
chmod 666 /var/run/docker.sock
```

### Windows-Specific Issues

**Docker Desktop on Windows**:
- Docker Desktop uses a named pipe, not a Unix socket
- Use Docker Desktop's WSL2 backend for better compatibility
- Or install Docker inside the Jenkins container (Option 3)

**WSL2 Backend**:
1. Enable WSL2 in Docker Desktop settings
2. Use WSL2 path for socket: `//var/run/docker.sock`

## Recommended Setup

For **development/testing**:
- Use **Option 1** (Docker Pipeline Plugin) - easiest and most reliable

For **production**:
- Use **Option 2** (Mount Docker Socket) with proper security
- Install Docker Pipeline plugin for better integration
- Use Kubernetes agents for scalable builds

## Next Steps

After setting up Docker:

1. **Restart Jenkins** (if you changed the container)
2. **Test Pipeline**: Run your pipeline again
3. **Verify**: Check that linting and tests run successfully

The pipeline will now be able to:
- ✅ Run linting in Python containers
- ✅ Run unit tests in isolated environments
- ✅ Build Docker images
- ✅ Run integration tests with docker-compose

