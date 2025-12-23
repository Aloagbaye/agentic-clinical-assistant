# Jenkins Credentials Setup Guide

Complete guide to setting up credentials in Jenkins for the agentic clinical assistant pipeline.

## Overview

The Jenkinsfile requires three types of credentials, but **they're all optional for local testing**:

1. **docker-credentials**: Docker registry login (username/password)
2. **docker-registry-url**: Docker registry URL
3. **kubeconfig**: Kubernetes configuration file

## Quick Answer

### docker-credentials

**What it is**: Username and password to log into a Docker registry (like Docker Hub, AWS ECR, etc.)

**What value to use**: 
- **For Docker Hub**: Your Docker Hub username and password (or access token)
- **For AWS ECR**: AWS access key ID and secret access key
- **For Azure ACR**: Service principal username and password
- **For testing**: You can skip this if you're not pushing images

**How to create**:
1. Go to: Manage Jenkins → Credentials → Add
2. Kind: **Username with password**
3. ID: `docker-credentials` (must match exactly)
4. Username: Your Docker Hub username (or registry username)
5. Password: Your Docker Hub password or access token
6. Click OK

### docker-registry-url

**What it is**: The URL of your Docker registry where images will be pushed.

**How to get it**:
- **Docker Hub**: `docker.io` or leave empty (defaults to Docker Hub)
- **AWS ECR**: `123456789012.dkr.ecr.us-east-1.amazonaws.com`
- **Azure ACR**: `yourregistry.azurecr.io`
- **Google GCR**: `gcr.io` or `us.gcr.io`
- **For testing**: You can skip this if you're not pushing images

**How to create**:
1. Go to: Manage Jenkins → Credentials → Add
2. Kind: **Secret text**
3. ID: `docker-registry-url` (must match exactly)
4. Secret: Your registry URL (e.g., `docker.io` or `yourregistry.azurecr.io`)
5. Click OK

## Detailed Setup

### Option 1: Docker Hub (Most Common)

#### Step 1: Get Docker Hub Credentials

1. **Create Docker Hub Account** (if you don't have one):
   - Go to https://hub.docker.com
   - Sign up for free account

2. **Get Access Token** (recommended over password):
   - Log into Docker Hub
   - Go to Account Settings → Security
   - Click "New Access Token"
   - Name: `jenkins-ci`
   - Permissions: Read & Write
   - Copy the token (you'll only see it once!)

#### Step 2: Create Credentials in Jenkins

**docker-credentials**:
1. Manage Jenkins → Credentials → Add
2. Kind: **Username with password**
3. Scope: Global
4. Username: Your Docker Hub username
5. Password: Your Docker Hub access token (or password)
6. ID: `docker-credentials`
7. Description: "Docker Hub credentials"
8. Click OK

**docker-registry-url**:
1. Manage Jenkins → Credentials → Add
2. Kind: **Secret text**
3. Scope: Global
4. Secret: `docker.io` (or leave empty for Docker Hub default)
5. ID: `docker-registry-url`
6. Description: "Docker Hub registry URL"
7. Click OK

### Option 2: AWS ECR (Amazon Elastic Container Registry)

#### Get ECR Credentials

1. **Get AWS Access Keys**:
   - AWS Console → IAM → Users → Your User
   - Security Credentials → Create Access Key
   - Save Access Key ID and Secret Access Key

2. **Get ECR Registry URL**:
   - AWS Console → ECR → Repositories
   - Click on your repository
   - Copy the "Repository URI" (e.g., `123456789012.dkr.ecr.us-east-1.amazonaws.com/your-repo`)

#### Create Credentials in Jenkins

**docker-credentials**:
- Username: Your AWS Access Key ID
- Password: Your AWS Secret Access Key
- ID: `docker-credentials`

**docker-registry-url**:
- Secret: Your ECR registry URL (e.g., `123456789012.dkr.ecr.us-east-1.amazonaws.com`)
- ID: `docker-registry-url`

### Option 3: Azure Container Registry (ACR)

#### Get ACR Credentials

1. **Get ACR Login Server**:
   - Azure Portal → Container Registries → Your Registry
   - Copy "Login server" (e.g., `yourregistry.azurecr.io`)

2. **Get Service Principal** (or use Admin credentials):
   - Azure Portal → Container Registries → Your Registry → Access Keys
   - Enable Admin user
   - Copy Username and Password

#### Create Credentials in Jenkins

**docker-credentials**:
- Username: ACR admin username
- Password: ACR admin password
- ID: `docker-credentials`

**docker-registry-url**:
- Secret: Your ACR login server (e.g., `yourregistry.azurecr.io`)
- ID: `docker-registry-url`

### Option 4: Skip for Local Testing

**You don't need these credentials if you're just testing locally!**

The updated Jenkinsfile will:
- Skip the "Push Images" stage if credentials aren't configured
- Skip the "Deploy to Dev" stage if kubeconfig isn't configured
- Skip Slack notifications if Slack plugin isn't installed

## Kubernetes Config (kubeconfig)

### What it is

A file that contains credentials and configuration for accessing a Kubernetes cluster.

### How to get it

**If you have kubectl configured locally**:

```powershell
# Copy your kubeconfig file
Copy-Item $env:USERPROFILE\.kube\config .\kubeconfig
```

**Or get from cloud provider**:

- **AWS EKS**: `aws eks update-kubeconfig --name your-cluster --region us-east-1`
- **Azure AKS**: `az aks get-credentials --resource-group your-rg --name your-cluster`
- **Google GKE**: `gcloud container clusters get-credentials your-cluster --zone us-central1-a`

### Create in Jenkins

1. Manage Jenkins → Credentials → Add
2. Kind: **Secret file**
3. ID: `kubeconfig`
4. File: Upload your kubeconfig file
5. Click OK

## Testing Without Credentials

The updated Jenkinsfile now handles missing credentials gracefully:

1. **No docker-credentials**: Images build but won't be pushed
2. **No docker-registry-url**: Push stage is skipped
3. **No kubeconfig**: Deployment stage is skipped
4. **No Slack plugin**: Notifications are skipped

You can test the pipeline with just:
- Git repository access
- Docker for building images
- Python for running tests

## Verification

### Check Credentials Exist

1. Go to: Manage Jenkins → Credentials
2. Under "System" → "Global credentials"
3. Verify you see:
   - `docker-credentials` (if configured)
   - `docker-registry-url` (if configured)
   - `kubeconfig` (if configured)

### Test Pipeline

1. Run pipeline build
2. Check console output
3. If credentials are missing, those stages will be skipped (not fail)

## Common Issues

### Error: "Credentials not found"

**Cause**: Credential ID doesn't match exactly.

**Solution**: 
- Check credential ID matches exactly: `docker-credentials`, `docker-registry-url`, `kubeconfig`
- IDs are case-sensitive

### Error: "Authentication failed"

**Cause**: Wrong username/password or expired token.

**Solution**:
- Verify credentials are correct
- For Docker Hub, use access token instead of password
- Check if token has expired

### Error: "Registry URL not found"

**Cause**: Wrong registry URL format.

**Solution**:
- Docker Hub: Use `docker.io` or leave empty
- ECR: Use full registry URL without `https://`
- ACR: Use login server URL

## Quick Reference

| Credential | Type | Example Value | Required? |
|------------|------|---------------|-----------|
| docker-credentials | Username/Password | Docker Hub username + token | No (for testing) |
| docker-registry-url | Secret text | `docker.io` or `yourregistry.azurecr.io` | No (for testing) |
| kubeconfig | Secret file | Upload kubeconfig file | No (for testing) |

## Next Steps

1. **For Local Testing**: Skip credentials, pipeline will work without them
2. **For Production**: Set up credentials for your registry
3. **For Deployment**: Configure kubeconfig for your cluster

The pipeline is now flexible and will work with or without credentials!

