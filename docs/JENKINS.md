# Jenkins Tutorial

Complete guide to setting up and using Jenkins for CI/CD with the agentic clinical assistant system.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Pipeline Setup](#pipeline-setup)
5. [Pipeline Stages](#pipeline-stages)
6. [Nightly Jobs](#nightly-jobs)
7. [Notifications](#notifications)
8. [Troubleshooting](#troubleshooting)

## Introduction

Jenkins is an open-source automation server that enables continuous integration and continuous deployment (CI/CD) for the agentic clinical assistant system.

### Key Features

- **Pipeline as Code**: Define builds using Jenkinsfile
- **Multi-stage Pipelines**: Lint, test, build, deploy
- **Docker Integration**: Build and push container images
- **Kubernetes Deployment**: Deploy to K8s clusters
- **Scheduled Jobs**: Nightly evaluation runs

## Installation

### Option 1: Docker

**Linux/Mac (Bash)**:
```bash
docker run -d \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

**Windows (PowerShell)**:
```powershell
# Use the provided script (recommended)
powershell scripts/start_jenkins.ps1

# Or manually:
docker run -d `
  --name jenkins `
  -p 8080:8080 `
  -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  jenkins/jenkins:lts
```

### Option 2: Package Manager

**Windows**:
```powershell
# Download Jenkins installer from https://www.jenkins.io/download/
# Run jenkins.msi installer
```

**Linux (Ubuntu/Debian)**:
```bash
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io-2023.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt-get update
sudo apt-get install jenkins
```

**Mac (Homebrew)**:
```bash
brew install jenkins-lts
```

### Option 3: Kubernetes

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: jenkins
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
  namespace: jenkins
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts
        ports:
        - containerPort: 8080
        - containerPort: 50000
        volumeMounts:
        - name: jenkins-home
          mountPath: /var/jenkins_home
      volumes:
      - name: jenkins-home
        persistentVolumeClaim:
          claimName: jenkins-pvc
```

## Configuration

### 1. Initial Setup

1. **Access Jenkins**:
   - Navigate to http://localhost:8080
   - Get initial admin password:
     ```bash
     # Docker
     docker exec <container> cat /var/jenkins_home/secrets/initialAdminPassword
     
     # Linux
     sudo cat /var/lib/jenkins/secrets/initialAdminPassword
     ```

2. **Install Plugins**:
   - Install recommended plugins
   - Or install manually:
     - Docker Pipeline
     - Kubernetes
     - Git
     - Credentials Binding
     - Slack Notification

3. **Create Admin User**:
   - Set up admin account
   - Configure URL

### 2. Required Plugins

Install these plugins via Manage Jenkins → Plugins:

- **Docker Pipeline**: Docker integration
- **Kubernetes**: K8s deployment
- **Git**: Git integration
- **Credentials Binding**: Secure credential management
- **Slack Notification**: Slack alerts
- **JUnit**: Test result reporting
- **Cobertura**: Code coverage
- **Pipeline**: Pipeline support

### 3. Configure Credentials

1. **Docker Registry**:
   - Manage Jenkins → Credentials → Add
   - Kind: Username with password
   - ID: `docker-credentials`
   - Username: Docker registry username
   - Password: Docker registry password

2. **Kubernetes Config**:
   - Manage Jenkins → Credentials → Add
   - Kind: Secret file
   - ID: `kubeconfig`
   - File: Upload kubeconfig file

3. **Docker Registry URL**:
   - Manage Jenkins → Credentials → Add
   - Kind: Secret text
   - ID: `docker-registry-url`
   - Secret: Registry URL (e.g., `registry.example.com`)

4. **Slack Webhook** (Optional):
   - Manage Jenkins → Credentials → Add
   - Kind: Secret text
   - ID: `slack-webhook`
   - Secret: Slack webhook URL

## Pipeline Setup

### 1. Create Pipeline Job

1. **New Item**:
   - Click "New Item"
   - Enter name: `agentic-clinical-assistant`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline**:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your Git repository URL
   - **Credentials**: Add Git credentials if needed
   - **Branches**: `*/develop` (or your main branch)
   - **Script Path**: `Jenkinsfile`

3. **Save and Build**:
   - Click Save
   - Click "Build Now"

### 2. Pipeline Stages Overview

The Jenkinsfile defines these stages:

1. **Checkout**: Get source code
2. **Lint & Format Check**: Code quality checks
3. **Unit Tests**: Run unit tests with coverage
4. **Integration Tests**: Test with Docker Compose
5. **Contract Tests**: Schema consistency tests
6. **Build Docker Images**: Build API and worker images
7. **Push Images**: Push to registry
8. **Deploy to Dev**: Deploy to Kubernetes (develop branch)
9. **Smoke Tests**: Verify deployment

## Pipeline Stages

### Stage 1: Checkout

```groovy
stage('Checkout') {
    steps {
        checkout scm
        script {
            env.GIT_COMMIT_SHORT = sh(
                script: 'git rev-parse --short HEAD',
                returnStdout: true
            ).trim()
        }
    }
}
```

**What it does**:
- Checks out source code from Git
- Gets short commit hash for tagging

### Stage 2: Lint & Format Check

```groovy
stage('Lint & Format Check') {
    steps {
        script {
            docker.image("python:${PYTHON_VERSION}").inside {
                sh '''
                    pip install black ruff isort mypy
                    black --check src/ tests/
                    ruff check src/ tests/
                    isort --check-only src/ tests/
                    mypy src/ --ignore-missing-imports
                '''
            }
        }
    }
}
```

**What it does**:
- Checks code formatting (black)
- Lints code (ruff)
- Checks import sorting (isort)
- Type checks (mypy)

### Stage 3: Unit Tests

```groovy
stage('Unit Tests') {
    steps {
        script {
            docker.image("python:${PYTHON_VERSION}").inside {
                sh '''
                    pip install -e ".[dev]"
                    pytest tests/unit/ -v --cov=src/agentic_clinical_assistant \
                        --cov-report=xml --cov-report=html \
                        --cov-report=term --junitxml=test-results.xml
                '''
            }
        }
    }
    post {
        always {
            junit 'test-results.xml'
            publishCoverage adapters: [
                coberturaAdapter('coverage.xml')
            ]
        }
    }
}
```

**What it does**:
- Runs unit tests
- Generates coverage reports
- Publishes test results and coverage

### Stage 4: Integration Tests

```groovy
stage('Integration Tests') {
    steps {
        script {
            sh '''
                docker-compose -f docker-compose.test.yml up -d
                sleep 10
                docker-compose -f docker-compose.test.yml exec -T api pytest tests/integration/ -v
            '''
        }
    }
    post {
        always {
            sh 'docker-compose -f docker-compose.test.yml down -v'
        }
    }
}
```

**What it does**:
- Starts test environment with Docker Compose
- Runs integration tests
- Cleans up test environment

### Stage 5: Contract Tests

```groovy
stage('Contract Tests') {
    steps {
        script {
            sh '''
                docker-compose -f docker-compose.test.yml up -d
                sleep 10
                pytest tests/contract/ -v
            '''
        }
    }
    post {
        always {
            sh 'docker-compose -f docker-compose.test.yml down -v'
        }
    }
}
```

**What it does**:
- Tests schema consistency
- Verifies verifier behavior
- Ensures API contract compliance

### Stage 6: Build Docker Images

```groovy
stage('Build Docker Images') {
    parallel {
        stage('Build API Image') {
            steps {
                script {
                    docker.build("agentic-clinical-assistant/api:${IMAGE_TAG}", "-f docker/Dockerfile.api .")
                    docker.build("agentic-clinical-assistant/api:latest", "-f docker/Dockerfile.api .")
                }
            }
        }
        stage('Build Worker Image') {
            steps {
                script {
                    docker.build("agentic-clinical-assistant/worker:${IMAGE_TAG}", "-f docker/Dockerfile.worker .")
                    docker.build("agentic-clinical-assistant/worker:latest", "-f docker/Dockerfile.worker .")
                }
            }
        }
    }
}
```

**What it does**:
- Builds API and worker images in parallel
- Tags with build number and commit hash
- Tags as latest

### Stage 7: Push Images

```groovy
stage('Push Images') {
    steps {
        script {
            withCredentials([usernamePassword(credentialsId: 'docker-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                sh '''
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin $DOCKER_REGISTRY
                    docker push agentic-clinical-assistant/api:${IMAGE_TAG}
                    docker push agentic-clinical-assistant/api:latest
                    docker push agentic-clinical-assistant/worker:${IMAGE_TAG}
                    docker push agentic-clinical-assistant/worker:latest
                '''
            }
        }
    }
}
```

**What it does**:
- Logs into Docker registry
- Pushes images to registry

### Stage 8: Deploy to Dev

```groovy
stage('Deploy to Dev') {
    when {
        branch 'develop'
    }
    steps {
        script {
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                sh '''
                    kubectl set image deployment/agent-api \
                        agent-api=agentic-clinical-assistant/api:${IMAGE_TAG} \
                        --namespace=dev
                    kubectl set image deployment/worker \
                        worker=agentic-clinical-assistant/worker:${IMAGE_TAG} \
                        --namespace=dev
                    kubectl rollout status deployment/agent-api --namespace=dev
                    kubectl rollout status deployment/worker --namespace=dev
                '''
            }
        }
    }
}
```

**What it does**:
- Only runs on develop branch
- Updates Kubernetes deployments
- Waits for rollout to complete

### Stage 9: Smoke Tests

```groovy
stage('Smoke Tests') {
    when {
        branch 'develop'
    }
    steps {
        script {
            sh '''
                sleep 30
                pytest tests/smoke/ -v --maxfail=1
                python scripts/ci/check_citations.py
                python scripts/ci/check_phi_leakage.py
            '''
        }
    }
}
```

**What it does**:
- Runs smoke tests
- Checks for citations
- Verifies no PHI leakage

## Nightly Jobs

### 1. Create Nightly Evaluation Job

1. **New Item**:
   - Click "New Item"
   - Name: `nightly-evaluation`
   - Type: Pipeline
   - Click OK

2. **Configure**:
   - **Definition**: Pipeline script
   - **Script**:
   ```groovy
   pipeline {
       agent any
       
       triggers {
           cron('0 2 * * *')  // 2 AM daily
       }
       
       stages {
           stage('Run Evaluation') {
               steps {
                   sh '''
                       export DATABASE_URL="${DATABASE_URL}"
                       export CELERY_BROKER_URL="${CELERY_BROKER_URL}"
                       python -m agentic_clinical_assistant.workers.tasks.evaluation run_nightly_evaluation
                   '''
               }
           }
           
           stage('Publish Results') {
               steps {
                   sh '''
                       # Publish to Prometheus
                       # Publish to Postgres
                       python scripts/ci/publish_evaluation_results.py
                   '''
               }
           }
       }
   }
   ```

3. **Save**:
   - Click Save

### 2. Manual Trigger

You can also trigger manually:
- Click "Build Now" on the job

## Notifications

### Slack Integration

1. **Install Slack Plugin**:
   - Manage Jenkins → Plugins
   - Install "Slack Notification"

2. **Configure Slack**:
   - Manage Jenkins → Configure System
   - Slack section:
     - Workspace: Your workspace
     - Credential: Add Slack webhook
     - Channel: #deployments

3. **Pipeline Notifications**:
   The Jenkinsfile includes:
   ```groovy
   post {
       success {
           slackSend(
               color: 'good',
               message: "✅ Build #${env.BUILD_NUMBER} succeeded",
               channel: '#deployments'
           )
       }
       failure {
           slackSend(
               color: 'danger',
               message: "❌ Build #${env.BUILD_NUMBER} failed",
               channel: '#deployments'
           )
       }
   }
   ```

### Email Notifications

1. **Configure SMTP**:
   - Manage Jenkins → Configure System
   - E-mail Notification:
     - SMTP server: smtp.example.com
     - Default user e-mail suffix: @example.com

2. **Add Recipients**:
   - In job configuration
   - Post-build Actions → E-mail Notification
   - Add recipient emails

## Troubleshooting

### Build Failures

1. **Check Logs**:
   - Click on failed build
   - View Console Output

2. **Common Issues**:
   - **Docker not available**: Install Docker plugin, ensure Docker is running
   - **Credentials not found**: Verify credential IDs match
   - **Tests failing**: Check test logs, fix failing tests
   - **Kubernetes connection**: Verify kubeconfig is correct

### Pipeline Not Running

1. **Check Triggers**:
   - Verify branch matches pipeline configuration
   - Check if manual trigger is required

2. **Check Permissions**:
   - Ensure user has build permissions
   - Verify Git credentials are correct

### Docker Build Failures

1. **Check Dockerfile**:
   - Verify Dockerfile syntax
   - Test build locally first

2. **Check Resources**:
   - Ensure sufficient disk space
   - Check Docker daemon is running

### Deployment Failures

1. **Check Kubernetes**:
   - Verify cluster is accessible
   - Check namespace exists
   - Verify deployment manifests

2. **Check Images**:
   - Ensure images are pushed to registry
   - Verify image tags are correct

## Best Practices

1. **Pipeline Organization**:
   - Keep stages focused and atomic
   - Use parallel stages where possible
   - Add proper error handling

2. **Credentials Management**:
   - Never hardcode credentials
   - Use Jenkins credential store
   - Rotate credentials regularly

3. **Testing**:
   - Run tests in isolated environments
   - Clean up test resources
   - Use appropriate test markers

4. **Deployment**:
   - Deploy to dev first
   - Use blue-green deployments
   - Monitor rollouts

5. **Notifications**:
   - Set up alerts for failures
   - Include relevant context
   - Avoid alert fatigue

## Advanced Features

### Multi-branch Pipeline

For multiple branches:

1. **Create Multi-branch Pipeline**:
   - New Item → Multibranch Pipeline
   - Configure branch sources
   - Set script path to Jenkinsfile

### Pipeline Libraries

For reusable code:

1. **Create Shared Library**:
   ```groovy
   // vars/buildImage.groovy
   def call(String imageName, String dockerfile) {
       docker.build("${imageName}:${env.BUILD_NUMBER}", "-f ${dockerfile} .")
   }
   ```

2. **Use in Pipeline**:
   ```groovy
   @Library('shared-library') _
   buildImage('api', 'docker/Dockerfile.api')
   ```

### Blue-Green Deployment

For zero-downtime deployments:

```groovy
stage('Blue-Green Deploy') {
    steps {
        sh '''
            # Deploy to green
            kubectl apply -f k8s/green/
            
            # Wait for readiness
            kubectl wait --for=condition=ready pod -l app=api-green
            
            # Switch traffic
            kubectl patch service api -p '{"spec":{"selector":{"version":"green"}}}'
            
            # Scale down blue
            kubectl scale deployment api-blue --replicas=0
        '''
    }
}
```

## Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Pipeline Plugin](https://plugins.jenkins.io/docker-workflow/)
- [Kubernetes Plugin](https://plugins.jenkins.io/kubernetes/)

