# Testing Jenkinsfile

Guide to testing and validating the Jenkinsfile locally before deploying to Jenkins.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Method 1: Jenkins CLI Validation](#method-1-jenkins-cli-validation)
3. [Method 2: Jenkinsfile Runner](#method-2-jenkinsfile-runner)
4. [Method 3: Local Jenkins Instance](#method-3-local-jenkins-instance)
5. [Method 4: Stage-by-Stage Testing](#method-4-stage-by-stage-testing)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Jenkins installed and running (for CLI validation)
- Java installed (for Jenkins CLI)
- Docker installed (for Jenkinsfile Runner or local Jenkins)
- Git repository with Jenkinsfile

## Method 1: Jenkins CLI Validation

### Quick Syntax Check

**Linux/Mac**:
```bash
# Download jenkins-cli.jar
wget http://localhost:8080/jnlpJars/jenkins-cli.jar

# Validate syntax
java -jar jenkins-cli.jar -s http://localhost:8080 \
  -auth admin:PASSWORD \
  declarative-linter < Jenkinsfile
```

**Windows (PowerShell)**:
```powershell
# Download jenkins-cli.jar
Invoke-WebRequest -Uri "http://localhost:8080/jnlpJars/jenkins-cli.jar" -OutFile "jenkins-cli.jar"

# Validate syntax
$password = Get-Content "$env:USERPROFILE\.jenkins\secrets\initialAdminPassword"
java -jar jenkins-cli.jar -s http://localhost:8080 -auth "admin:$password" declarative-linter < Jenkinsfile
```

**Using Scripts**:
```bash
# Linux/Mac
bash scripts/test_jenkinsfile.sh

# Windows
powershell scripts/test_jenkinsfile.ps1
```

### Expected Output

```
Jenkinsfile successfully validated.
```

## Method 2: Jenkinsfile Runner

Jenkinsfile Runner allows you to run a Jenkinsfile locally without a full Jenkins installation.

### Installation

```bash
# Download Jenkinsfile Runner
wget https://github.com/jenkinsci/jenkinsfile-runner/releases/download/1.0-beta-29/jenkinsfile-runner-1.0-beta-29.tar.gz
tar -xzf jenkinsfile-runner-1.0-beta-29.tar.gz
cd jenkinsfile-runner
```

### Run Jenkinsfile

```bash
jenkinsfile-runner \
  --file ../Jenkinsfile \
  --job-dsl ../job-dsl/ \
  --plugins plugins.txt
```

### Limitations

- Some plugins may not be available
- Kubernetes deployment stages will fail (no cluster)
- Docker builds require Docker daemon

## Method 3: Local Jenkins Instance

### Using Docker

**Linux/Mac (Bash)**:
```bash
# Start Jenkins
docker run -d \
  -p 8082:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

# Get initial password
docker exec <container> cat /var/jenkins_home/secrets/initialAdminPassword
```

**Windows (PowerShell)**:
```powershell
# Start Jenkins
docker run -d `
  -p 8080:8080 `
  -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  -v //var/run/docker.sock:/var/run/docker.sock `
  jenkins/jenkins:lts

# Get initial password
docker exec <container> cat /var/jenkins_home/secrets/initialAdminPassword
```

Or use the provided script:
```powershell
powershell scripts/start_jenkins.ps1
```

### Create Pipeline Job

1. **Access Jenkins**: http://localhost:8080 (or your Jenkins URL)
2. **Create Pipeline**:
   - Click "New Item"
   - Enter name: `agentic-clinical-assistant`
   - Select "Pipeline"
   - Click OK
3. **Configure Pipeline**:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL (e.g., `https://github.com/yourusername/agentic-clinical-assistant.git`)
   - **Credentials**: Add Git credentials if repository is private
   - **Branches to build**: 
     - **Branch Specifier**: `*/develop` or `*/main` (NOT `**` or `refs/heads/**`)
     - Or use: `*/master`, `*/main`, `*/develop` depending on your default branch
   - **Script Path**: `Jenkinsfile`
   - Click Save
4. **Build Now**: Click "Build Now" to test the pipeline

### Important: Branch Specifier

**Common Error**: `Invalid refspec refs/heads/**`

**Solution**: Use a valid branch pattern:
- ✅ `*/develop` - Builds from develop branch
- ✅ `*/main` - Builds from main branch  
- ✅ `*/master` - Builds from master branch
- ✅ `*/feature/*` - Builds from any feature branch
- ❌ `**` - Invalid (causes the error)
- ❌ `refs/heads/**` - Invalid (causes the error)

**For testing, use**: `*/main` or `*/develop` depending on your default branch.

### Test Individual Stages

1. **Blue Ocean UI**: http://localhost:8080/blue
2. **Create Pipeline**: From Jenkinsfile
3. **Run Stages**: Click on individual stages to test

## Method 4: Stage-by-Stage Testing

### Test Stages Locally

#### 1. Checkout Stage

```bash
# Manual checkout
git clone <repo-url>
cd <repo>
git checkout <branch>
```

#### 2. Lint & Format Check

```bash
# Install tools
pip install black ruff isort mypy

# Run checks
black --check src/ tests/
ruff check src/ tests/
isort --check-only src/ tests/
mypy src/ --ignore-missing-imports
```

#### 3. Unit Tests

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/unit/ -v --cov=src/agentic_clinical_assistant \
  --cov-report=xml --cov-report=html
```

#### 4. Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests
docker-compose -f docker-compose.test.yml exec -T api pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

#### 5. Build Docker Images

```bash
# Build API image
docker build -f docker/Dockerfile.api -t agentic-clinical-assistant/api:test .

# Build worker image
docker build -f docker/Dockerfile.worker -t agentic-clinical-assistant/worker:test .

# Verify images
docker images | grep agentic-clinical-assistant
```

#### 6. Push Images (Test)

```bash
# Tag for test registry
docker tag agentic-clinical-assistant/api:test localhost:5000/api:test
docker tag agentic-clinical-assistant/worker:test localhost:5000/worker:test

# Push to local registry (if running)
docker push localhost:5000/api:test
docker push localhost:5000/worker:test
```

#### 7. Deploy to K8s (Test)

```bash
# Apply manifests
kubectl apply -k k8s/overlays/dev/

# Check deployment
kubectl get deployments -n dev
kubectl get pods -n dev

# Check logs
kubectl logs -f deployment/agent-api -n dev
```

#### 8. Smoke Tests

```bash
# Run smoke tests
pytest tests/smoke/ -v

# Check citations
python scripts/ci/check_citations.py http://localhost:8000

# Check PHI leakage
python scripts/ci/check_phi_leakage.py http://localhost:8000
```

## Testing Without Full Setup

### Skip Deployment Stages

Create a test Jenkinsfile that skips deployment:

```groovy
stage('Deploy to Dev') {
    when {
        branch 'develop'
        // Skip if no K8s access
        expression { return false }
    }
    steps {
        echo "Skipping deployment in test mode"
    }
}
```

### Mock External Services

Use test doubles for:
- Docker registry (local registry)
- Kubernetes (kind or minikube)
- Secrets (test credentials)

## Troubleshooting

### Common Issues

**Issue**: `Invalid refspec refs/heads/**`
- **Solution**: In pipeline configuration, change branch specifier from `**` to `*/main` or `*/develop`
- **See**: [Invalid Refspec Error](#invalid-refspec-error) section below

**Issue**: "Jenkinsfile validation failed"
- **Solution**: Check syntax, ensure all stages are properly closed

**Issue**: "Credentials not found"
- **Solution**: Create test credentials in Jenkins or skip credential stages

**Issue**: "Docker build fails"
- **Solution**: Ensure Docker daemon is running, check Dockerfile syntax

**Issue**: "Kubernetes deployment fails"
- **Solution**: Verify kubeconfig, check cluster connectivity

**Issue**: "Tests fail"
- **Solution**: Run tests locally first, check test environment

### Invalid Refspec Error

**Error Message**:
```
java.lang.IllegalArgumentException: Invalid refspec refs/heads/**
```

**Cause**: The branch specifier in Jenkins job configuration uses an invalid pattern (`**`).

**Solution**:
1. Go to your pipeline job → Configure
2. Find "Branches to build" or "Branch Specifier"
3. Change from: `**` or `refs/heads/**`
4. Change to: `*/main` or `*/develop` (your actual branch name)
5. Save and rebuild

**Valid Branch Patterns**:
- `*/main` - Builds from main branch
- `*/develop` - Builds from develop branch
- `*/master` - Builds from master branch
- `*/feature/*` - Builds from any feature branch

**Invalid Patterns** (will cause error):
- `**` ❌
- `refs/heads/**` ❌
- `*/**` ❌

### Debug Tips

1. **Add Echo Statements**:
   ```groovy
   stage('Debug') {
       steps {
           echo "Environment: ${env.BUILD_NUMBER}"
           echo "Branch: ${env.BRANCH_NAME}"
       }
   }
   ```

2. **Check Logs**:
   - View console output in Jenkins
   - Check Docker logs: `docker logs <container>`
   - Check K8s logs: `kubectl logs <pod>`

3. **Validate Manually**:
   - Test each command from pipeline locally
   - Verify file paths and permissions
   - Check environment variables

## Best Practices

1. **Test Locally First**: Run stages manually before committing
2. **Use Test Branches**: Create test branches for pipeline changes
3. **Incremental Testing**: Test one stage at a time
4. **Mock External Services**: Use local alternatives when possible
5. **Version Control**: Commit working Jenkinsfile versions

## Next Steps

After validating the Jenkinsfile:

1. Set up Jenkins server (if not done)
2. Configure credentials
3. Create pipeline job
4. Run first build
5. Monitor and iterate

## Resources

- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Jenkinsfile Runner](https://github.com/jenkinsci/jenkinsfile-runner)
- [Jenkins CLI](https://www.jenkins.io/doc/book/managing/cli/)

