pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = credentials('docker-registry-url')
        DOCKER_CREDENTIALS = credentials('docker-credentials')
        KUBECONFIG = credentials('kubeconfig')
        PYTHON_VERSION = '3.12'
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    }
    
    options {
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }
    
    stages {
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
        
        stage('Lint & Format Check') {
            steps {
                script {
                    docker.image("python:${PYTHON_VERSION}").inside {
                        sh '''
                            pip install --upgrade pip
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
        
        stage('Unit Tests') {
            steps {
                script {
                    docker.image("python:${PYTHON_VERSION}").inside {
                        sh '''
                            pip install --upgrade pip
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
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
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
        
        stage('Smoke Tests') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    sh '''
                        # Wait for deployment to be ready
                        sleep 30
                        
                        # Run smoke tests
                        pytest tests/smoke/ -v --maxfail=1
                        
                        # Check for citations in responses
                        python scripts/ci/check_citations.py
                        
                        # Check for PHI in logs
                        python scripts/ci/check_phi_leakage.py
                    '''
                }
            }
        }
    }
    
    post {
        success {
            script {
                if (env.BRANCH_NAME == 'develop') {
                    slackSend(
                        color: 'good',
                        message: "✅ Build #${env.BUILD_NUMBER} succeeded and deployed to dev",
                        channel: '#deployments'
                    )
                }
            }
        }
        failure {
            script {
                slackSend(
                    color: 'danger',
                    message: "❌ Build #${env.BUILD_NUMBER} failed",
                    channel: '#deployments'
                )
            }
        }
        always {
            cleanWs()
        }
    }
}

