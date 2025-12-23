# Jenkins Plugins Setup

Guide to installing required plugins for the agentic clinical assistant pipeline.

## Required Plugins

The Jenkinsfile uses these plugins (all optional for basic testing):

1. **Docker Pipeline** - For building Docker images
2. **Slack Notification** - For build notifications (optional)
3. **Git** - For Git integration (usually pre-installed)
4. **JUnit** - For test result reporting (usually pre-installed)
5. **Cobertura** - For code coverage (usually pre-installed)

## Quick Install

### Method 1: Install via Jenkins UI

1. **Go to Jenkins**: http://localhost:8083
2. **Manage Jenkins** → **Plugins**
3. **Available** tab
4. **Search and install**:
   - `Docker Pipeline`
   - `Slack Notification` (optional)
5. **Restart Jenkins** if prompted

### Method 2: Install via Plugin Manager

1. **Manage Jenkins** → **Plugin Manager**
2. **Available** tab
3. **Filter**: Type plugin name
4. **Check** the plugins you want
5. **Install without restart** (or **Download now and install after restart**)
6. **Restart Jenkins** when done

## Plugin Details

### Docker Pipeline Plugin

**Required for**: Building Docker images in pipeline

**Install**:
1. Manage Jenkins → Plugins
2. Search: `Docker Pipeline`
3. Install
4. Restart Jenkins

**Alternative**: The updated Jenkinsfile will use `docker` command directly if plugin is not available.

### Slack Notification Plugin

**Required for**: Slack notifications (optional)

**Install**:
1. Manage Jenkins → Plugins
2. Search: `Slack Notification`
3. Install
4. Configure in: Manage Jenkins → Configure System → Slack

**Alternative**: The updated Jenkinsfile handles missing Slack plugin gracefully.

## Verify Installation

### Check Installed Plugins

1. **Manage Jenkins** → **Plugins**
2. **Installed** tab
3. Search for:
   - `Docker Pipeline`
   - `Slack Notification`

### Test Docker Pipeline

Create a test pipeline:

```groovy
pipeline {
    agent any
    stages {
        stage('Test Docker') {
            steps {
                script {
                    docker.image('hello-world').inside {
                        sh 'echo "Docker works!"'
                    }
                }
            }
        }
    }
}
```

If this works, Docker Pipeline plugin is installed correctly.

## Troubleshooting

### Error: "No such property: docker"

**Cause**: Docker Pipeline plugin not installed.

**Solution**:
1. Install Docker Pipeline plugin (see above)
2. Restart Jenkins
3. Or use the updated Jenkinsfile which handles this gracefully

### Error: "Docker command not found"

**Cause**: Docker is not installed or not accessible from Jenkins.

**Solution**:
1. **For Jenkins in Docker**: Ensure Docker socket is mounted
2. **For Jenkins on host**: Install Docker and ensure Jenkins user can access it
3. **For Windows**: Install Docker Desktop and ensure it's running

### Error: "No such DSL method 'slackSend'"

**Cause**: Slack Notification plugin not installed.

**Solution**:
1. Install Slack Notification plugin
2. Or ignore - the updated Jenkinsfile handles this gracefully

## Minimal Setup for Testing

**You can test the pipeline with minimal plugins:**

1. **Git** (usually pre-installed)
2. **JUnit** (usually pre-installed)
3. **Cobertura** (usually pre-installed)

**Optional**:
- Docker Pipeline (for Docker builds)
- Slack Notification (for notifications)

The updated Jenkinsfile will work with or without these plugins!

## Recommended Plugins

For a complete CI/CD setup:

- **Docker Pipeline** - Docker integration
- **Kubernetes** - K8s deployment
- **Git** - Source control
- **Credentials Binding** - Secure credentials
- **Slack Notification** - Notifications
- **JUnit** - Test reporting
- **Cobertura** - Coverage reporting
- **Pipeline** - Pipeline support
- **Blue Ocean** - Better UI (optional)

## Installation Script

You can also install plugins via CLI:

```bash
# List available plugins
java -jar jenkins-cli.jar -s http://localhost:8080 list-plugins

# Install plugin
java -jar jenkins-cli.jar -s http://localhost:8080 install-plugin docker-workflow
```

## Next Steps

After installing plugins:

1. **Restart Jenkins** (if prompted)
2. **Test Pipeline**: Run your pipeline again
3. **Check Logs**: Verify plugins are working

The updated Jenkinsfile is now more resilient and will work even if some plugins are missing!

