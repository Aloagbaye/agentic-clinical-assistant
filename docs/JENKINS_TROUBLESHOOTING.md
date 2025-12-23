# Jenkins Troubleshooting Guide

Common issues and solutions when setting up and running Jenkins pipelines.

## Table of Contents

1. [Invalid Refspec Error](#invalid-refspec-error)
2. [Git Checkout Failures](#git-checkout-failures)
3. [Docker Build Failures](#docker-build-failures)
4. [Credential Issues](#credential-issues)
5. [Pipeline Stage Failures](#pipeline-stage-failures)

## Invalid Refspec Error

### Error Message

```
java.lang.IllegalArgumentException: Invalid refspec refs/heads/**
```

### Cause

The branch specifier in Jenkins job configuration uses an invalid pattern. The `**` wildcard is not valid in Git refspecs.

### Solution

1. **Go to Pipeline Configuration**:
   - Open your pipeline job
   - Click "Configure"
   - Scroll to "Pipeline" section

2. **Fix Branch Specifier**:
   - Find "Branches to build" or "Branch Specifier"
   - Change from: `**` or `refs/heads/**`
   - Change to: `*/main` or `*/develop` (depending on your branch)

3. **Valid Branch Patterns**:
   ```
   */main          - Builds from main branch
   */develop       - Builds from develop branch
   */master        - Builds from master branch
   */feature/*     - Builds from any feature branch
   origin/main     - Specific branch from origin
   ```

4. **Save and Rebuild**:
   - Click "Save"
   - Click "Build Now"

### Example Configuration

**Correct Configuration**:
```
Repository URL: https://github.com/yourusername/agentic-clinical-assistant.git
Branch Specifier: */main
Script Path: Jenkinsfile
```

**Incorrect Configuration** (causes error):
```
Branch Specifier: **
Branch Specifier: refs/heads/**
Branch Specifier: */**  ❌
```

## Git Checkout Failures

### Error: Repository Not Found

**Cause**: Invalid repository URL or missing credentials.

**Solution**:
1. Verify repository URL is correct
2. For private repos, add credentials:
   - Manage Jenkins → Credentials → Add
   - Kind: Username with password
   - Enter Git username and password/token
   - Use credential ID in pipeline config

### Error: Permission Denied

**Cause**: No access to repository or invalid credentials.

**Solution**:
1. Check repository permissions
2. Use Personal Access Token instead of password
3. Verify credentials are correct

## Docker Build Failures

### Error: Cannot connect to Docker daemon

**Cause**: Docker is not running or Jenkins can't access Docker.

**Solution**:
1. **For Docker-in-Docker**:
   - Ensure Docker socket is mounted
   - Check Docker plugin is installed

2. **For Local Docker**:
   - Start Docker Desktop
   - Verify Docker is accessible: `docker ps`

3. **For Jenkins in Docker**:
   - Mount Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`
   - Add Jenkins user to docker group

### Error: Dockerfile not found

**Cause**: Jenkinsfile references Dockerfile that doesn't exist.

**Solution**:
1. Verify Dockerfile path in Jenkinsfile
2. Check file is in repository
3. Ensure correct working directory

## Credential Issues

### Error: Credentials not found

**Cause**: Credential ID doesn't exist or is incorrect.

**Solution**:
1. **Check Credential ID**:
   - Manage Jenkins → Credentials
   - Verify credential exists
   - Note the exact ID

2. **Update Jenkinsfile**:
   - Use correct credential ID
   - Format: `credentials('credential-id')`

3. **Create Missing Credentials**:
   - Manage Jenkins → Credentials → Add
   - Use same ID as in Jenkinsfile

### Common Credential IDs

Based on Jenkinsfile, you need:
- `docker-credentials` - Docker registry login
- `docker-registry-url` - Registry URL
- `kubeconfig` - Kubernetes config file

## Pipeline Stage Failures

### Lint Stage Fails

**Error**: Code formatting or linting issues.

**Solution**:
1. Run linting locally first:
   ```bash
   black --check src/ tests/
   ruff check src/ tests/
   ```

2. Fix issues or configure to be warnings only

### Unit Tests Fail

**Error**: Tests are failing.

**Solution**:
1. Run tests locally:
   ```bash
   pytest tests/unit/ -v
   ```

2. Fix failing tests
3. Check test environment matches Jenkins

### Integration Tests Fail

**Error**: Docker Compose or integration test failures.

**Solution**:
1. Test locally:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   pytest tests/integration/ -v
   ```

2. Check Docker Compose file syntax
3. Verify services start correctly

### Build Stage Fails

**Error**: Docker image build fails.

**Solution**:
1. Test build locally:
   ```bash
   docker build -f docker/Dockerfile.api -t test-api .
   ```

2. Check Dockerfile syntax
3. Verify all files are in repository
4. Check .dockerignore isn't excluding needed files

### Deployment Stage Fails

**Error**: Kubernetes deployment fails.

**Solution**:
1. **Verify kubeconfig**:
   - Check credential is correct
   - Test: `kubectl get nodes`

2. **Check Namespace**:
   - Ensure namespace exists: `kubectl create namespace dev`

3. **Verify Manifests**:
   - Test locally: `kubectl apply -k k8s/overlays/dev/ --dry-run=client`

4. **Check Permissions**:
   - Verify Jenkins has deployment permissions

## General Troubleshooting

### Check Jenkins Logs

```powershell
# View Jenkins container logs
docker logs jenkins --tail 100

# View specific build logs
# In Jenkins UI: Build → Console Output
```

### Verify Pipeline Syntax

```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar -s http://localhost:8080 \
  -auth admin:PASSWORD \
  declarative-linter < Jenkinsfile
```

### Test Stages Locally

Run each stage command manually to identify issues:

```bash
# Lint
black --check src/ tests/

# Tests
pytest tests/unit/ -v

# Build
docker build -f docker/Dockerfile.api -t test .
```

### Common Issues Checklist

- [ ] Branch specifier is valid (not `**`)
- [ ] Repository URL is correct
- [ ] Credentials are configured
- [ ] Docker is running
- [ ] Kubernetes cluster is accessible
- [ ] All required files are in repository
- [ ] Jenkins plugins are installed
- [ ] Pipeline syntax is correct

## Getting Help

1. **Check Console Output**: Most detailed error info
2. **Check Stage Logs**: Individual stage failures
3. **Test Locally**: Reproduce issues outside Jenkins
4. **Jenkins Logs**: `docker logs jenkins`
5. **Git Logs**: Check repository access

## Quick Fixes

### Reset Pipeline Job

1. Delete and recreate job
2. Re-enter all configuration
3. Verify branch specifier

### Clear Jenkins Workspace

```powershell
# Stop Jenkins
docker stop jenkins

# Remove workspace (if needed)
docker exec jenkins rm -rf /var/jenkins_home/workspace/*

# Start Jenkins
docker start jenkins
```

### Reinstall Plugins

1. Manage Jenkins → Plugins
2. Uninstall problematic plugin
3. Restart Jenkins
4. Reinstall plugin

