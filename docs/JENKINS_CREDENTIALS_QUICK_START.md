# Jenkins Credentials Quick Start

Quick guide to setting up Docker credentials in Jenkins.

## TL;DR - For Testing

**You don't need credentials for testing!** The updated Jenkinsfile will skip push/deploy stages if credentials aren't configured.

## What Are These Credentials?

### docker-credentials

**What it is**: Username and password to log into a Docker registry.

**What value to use**: 
- **For Docker Hub**: Your Docker Hub username + password (or access token)
- **For testing**: You can skip this entirely

**It's just a name you create in Jenkins** - you can use any username/password you want!

### docker-registry-url

**What it is**: The URL of your Docker registry.

**How to get it**:
- **Docker Hub**: `docker.io` (or leave empty)
- **AWS ECR**: `123456789012.dkr.ecr.us-east-1.amazonaws.com`
- **Azure ACR**: `yourregistry.azurecr.io`
- **For testing**: Skip this - pipeline will work without it

## Quick Setup (Docker Hub Example)

### Step 1: Create docker-credentials

1. **Go to Jenkins**: http://localhost:8083 (or your Jenkins URL)
2. **Manage Jenkins** → **Credentials**
3. **System** → **Global credentials (unrestricted)** → **Add Credentials**
4. **Fill in**:
   - **Kind**: Username with password
   - **Username**: Your Docker Hub username (e.g., `yourusername`)
   - **Password**: Your Docker Hub password or access token
   - **ID**: `docker-credentials` (must match exactly!)
   - **Description**: "Docker Hub credentials"
5. **Click OK**

### Step 2: Create docker-registry-url

1. **Add Credentials** again
2. **Fill in**:
   - **Kind**: Secret text
   - **Secret**: `docker.io` (for Docker Hub)
   - **ID**: `docker-registry-url` (must match exactly!)
   - **Description**: "Docker Hub registry URL"
3. **Click OK**

## That's It!

Now your pipeline can push images to Docker Hub.

## For Testing Without Credentials

**Just don't create them!** The pipeline will:
- ✅ Build images successfully
- ✅ Run all tests
- ⏭️ Skip push stage (no error)
- ⏭️ Skip deployment stage (no error)

## Common Registry URLs

| Registry | URL |
|----------|-----|
| Docker Hub | `docker.io` |
| AWS ECR | `123456789012.dkr.ecr.us-east-1.amazonaws.com` |
| Azure ACR | `yourregistry.azurecr.io` |
| Google GCR | `gcr.io` |
| GitHub Container Registry | `ghcr.io` |

## Getting Docker Hub Access Token (Recommended)

Instead of using your password, use an access token:

1. Go to https://hub.docker.com
2. Account Settings → Security
3. New Access Token
4. Name: `jenkins-ci`
5. Permissions: Read & Write
6. Copy the token (use this as password in Jenkins)

## Verification

After creating credentials:
1. Go to: Manage Jenkins → Credentials
2. You should see:
   - `docker-credentials` (username/password)
   - `docker-registry-url` (secret text)

## Next Steps

1. **For Testing**: Don't create credentials - pipeline works without them
2. **For Production**: Create credentials for your registry
3. **Run Pipeline**: It will use credentials if available, skip if not

The pipeline is now flexible and won't fail if credentials are missing!

