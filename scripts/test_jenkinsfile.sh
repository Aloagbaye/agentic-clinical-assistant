#!/bin/bash
# Script to test Jenkinsfile locally

set -e

echo "Testing Jenkinsfile..."

# Check if Jenkins CLI is available
if ! command -v jenkins-cli &> /dev/null; then
    echo "Jenkins CLI not found. Installing..."
    # Download jenkins-cli.jar
    wget http://localhost:8080/jnlpJars/jenkins-cli.jar -O jenkins-cli.jar || {
        echo "Error: Could not download jenkins-cli.jar"
        echo "Make sure Jenkins is running on localhost:8080"
        exit 1
    }
fi

# Validate Jenkinsfile syntax
echo "Validating Jenkinsfile syntax..."
java -jar jenkins-cli.jar -s http://localhost:8080 -auth admin:$(cat ~/.jenkins/secrets/initialAdminPassword) declarative-linter < Jenkinsfile || {
    echo "Jenkinsfile validation failed"
    exit 1
}

echo "✅ Jenkinsfile syntax is valid"

# Test individual stages (if using Jenkins Blue Ocean)
echo ""
echo "To test stages individually:"
echo "1. Open Jenkins Blue Ocean UI"
echo "2. Create a new pipeline from Jenkinsfile"
echo "3. Run individual stages"

# Alternative: Use Jenkinsfile Runner (if installed)
if command -v jenkinsfile-runner &> /dev/null; then
    echo ""
    echo "Running Jenkinsfile with Jenkinsfile Runner..."
    jenkinsfile-runner -f Jenkinsfile
else
    echo ""
    echo "Jenkinsfile Runner not installed."
    echo "Install from: https://github.com/jenkinsci/jenkinsfile-runner"
fi

