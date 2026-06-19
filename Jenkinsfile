pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Lint & Analyze') {
            parallel {
                stage('Backend - Lint') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Backend:/work" -w /work alpine:3.21 sh -c "
                                apk add --no-cache clang-extra-tools && \
                                find src -name '*.cpp' -o -name '*.h' -o -name '*.cc' \
                                    -exec clang-format --dry-run --Werror {} +
                            "
                        '''
                    }
                }

                stage('Client - Analyze & Test') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Client:/app" -w /app ghcr.io/cirruslabs/flutter:3.29.3 sh -c "
                                flutter pub get && flutter analyze && flutter test
                            "
                        '''
                    }
                }

                stage('Docs - Lint') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Docs:/work" -w /work python:3.12-alpine sh -c "
                                pip install poetry && \
                                poetry install --no-root && \
                                poetry run ruff check .
                            "
                        '''
                    }
                }

                stage('Kubernetes - Lint') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Kubernetes:/work" -w /work python:3.12-alpine sh -c "
                                wget -qO- https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz | tar xz && \
                                mv linux-amd64/helm /usr/local/bin/helm && \
                                for chart in apps/*/; do
                                    chart=\${chart%/}
                                    if [ -f \"\$chart/values-tst.yaml\" ]; then
                                        helm lint \"\$chart\" --values \"\$chart/values-tst.yaml\"
                                    else
                                        helm lint \"\$chart\"
                                    fi
                                done && \
                                pip install poetry && \
                                poetry install --no-root --with dev && \
                                poetry run ruff check stylist/ && \
                                poetry run pytest
                            "
                        '''
                    }
                }

                stage('Terraform - Validate') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Terraform:/work" -w /work --entrypoint= hashicorp/terraform:1.15.6 sh -c "
                                terraform fmt -check -recursive && \
                                terraform init -backend=false && \
                                terraform validate
                            "
                        '''
                    }
                }

                stage('Website - Lint') {
                    steps {
                        sh '''
                            docker run --rm -v "$PWD/Website:/work" -w /work php:8.4-cli-alpine sh -c "
                                php -r \"copy('https://getcomposer.org/installer', 'composer-setup.php');\" && \
                                php composer-setup.php --quiet && \
                                mv composer.phar /usr/local/bin/composer && \
                                composer install --no-interaction --prefer-dist && \
                                ./vendor/bin/pint --test
                            "
                        '''
                    }
                }
            }
        }

        stage('Backend - Build') {
            steps {
                dir('Backend') {
                    sh 'docker build -t salonmaster-backend .'
                }
            }
        }

        stage('Docs - Build') {
            steps {
                sh '''
                    docker run --rm -v "$PWD/Docs:/work" -w /work python:3.12-alpine sh -c "
                        pip install poetry && \
                        poetry install --no-root && \
                        poetry run mkdocs build --strict
                    "
                '''
            }
        }
    }

    post {
        always {
            cleanWs(patterns: [[pattern: '**', type: 'EXCLUDE']])
        }
    }
}
