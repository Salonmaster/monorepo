pipeline {
    agent any
    
    triggers {
        genericTrigger {
            token('salonmaster-webhook')
            genericVariables {
                genericVariable {
                    key('ref')
                    value('\$.ref')
                }
            }
            genericRequestVariables {
                genericRequestVariable {
                    key('scm_manager_branch')
                    regexpFilter('.*')
                }
            }
            regexpFilterText('\$ref')
            regexpFilterExpression('refs/heads/main')
            causeString('SCM-Manager push on \$ref')
            printContributedVariables(false)
            printPostContent(true)
            silentResponse(false)
        }
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }
    
    stages {
        stage('Backend - Build') {
            steps {
                dir('Backend') {
                    sh 'docker build -t salonmaster-backend .'
                }
            }
        }
        
        stage('Backend - Lint') {
            steps {
                dir('Backend') {
                    sh '''
                        find src -name "*.cpp" -o -name "*.h" -o -name "*.cc" | while read f; do
                            clang-format --dry-run --Werror "$f"
                        done
                    '''
                }
            }
        }
        
        stage('Client - Analyze & Test') {
            steps {
                dir('Client') {
                    sh 'flutter pub get && flutter analyze && flutter test'
                }
            }
        }
        
        stage('Docs - Build') {
            steps {
                dir('Docs') {
                    sh '''
                        pip install poetry
                        poetry install
                        poetry run mkdocs build --strict
                    '''
                }
            }
        }
        
        stage('Docs - Lint') {
            steps {
                dir('Docs') {
                    sh 'poetry run ruff check .'
                }
            }
        }
        
        stage('Kubernetes - Lint') {
            steps {
                dir('Kubernetes') {
                    sh '''
                        helm lint apps/*/
                        pip install poetry
                        poetry install
                        poetry run ruff check stylist/
                        poetry run pytest
                    '''
                }
            }
        }
        
        stage('Terraform - Validate') {
            steps {
                dir('Terraform') {
                    sh '''
                        terraform fmt -check -recursive
                        terraform init -backend=false
                        terraform validate
                    '''
                }
            }
        }
        
        stage('Website - Lint') {
            steps {
                dir('Website') {
                    sh '''
                        composer install --no-interaction --prefer-dist
                        ./vendor/bin/pint --test
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs(patterns: [[pattern: '**', type: 'EXCLUDE']])
        }
    }
}
