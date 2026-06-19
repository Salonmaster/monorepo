pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }

    environment {
        HARBOR_REGISTRY = 'harbor.void-zero.com'
        HARBOR_PROJECT = 'salonmaster'
    }

    stages {
        stage('Lint & Analyze') {
            parallel {
                stage('Backend - Lint') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Backend:/work:Z" -w /work alpine:3.21 sh -c "
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
                            docker run --rm \
                                -v "$PWD/Client:/app:Z" -w /app \
                                ghcr.io/cirruslabs/flutter:3.29.3 sh -c "
                                flutter pub get && flutter analyze && flutter test
                            "
                        '''
                    }
                }

                stage('Docs - Lint') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Docs:/work:Z" -w /work python:3.12-alpine sh -c "
                                pip install --upgrade pip poetry && \
                                poetry install --no-root && \
                                poetry run ruff check .
                            "
                        '''
                    }
                }

                stage('Kubernetes - Lint') {
                    steps {
                        sh '''
                            docker run -i --rm \
                                -v "$PWD/Kubernetes:/work:Z" -w /work python:3.12-alpine sh -s <<'HEREDOC_END'
wget -qO- https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz | tar xz
mv linux-amd64/helm /usr/local/bin/helm

for chart in apps/*/; do
    chart=${chart%/}
    if [ -f "$chart/values-tst.yaml" ]; then
        helm lint "$chart" --values "$chart/values-tst.yaml"
    else
        helm lint "$chart"
    fi
done

pip install --upgrade pip poetry
poetry install --no-root --with dev
poetry run ruff check stylist/
poetry run pytest
HEREDOC_END
                        '''
                    }
                }

                stage('Website - Lint') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Website:/app:Z" -w /app composer:2 sh -c "
                                composer install --no-interaction --prefer-dist && \
                                ./vendor/bin/pint --test
                            "
                        '''
                    }
                }
            }
        }

        stage('Build') {
            stages {
                stage('Backend - Build') {
                    steps {
                        dir('Backend') {
                            sh 'docker build -t salonmaster-backend .'
                        }
                    }
                }

                stage('Website - Build') {
                    steps {
                        dir('Website') {
                            sh 'docker build -t salonmaster-website .'
                        }
                    }
                }

                stage('Docs - Build Tech') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Docs:/work:Z" -w /work python:3.12-alpine sh -c "
                                pip install poetry && \
                                poetry install --no-root && \
                                poetry run mkdocs build --strict
                            "
                        '''
                    }
                }

                stage('Docs - Build User') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Docs/user:/work:Z" -w /work python:3.12-alpine sh -c "
                                pip install mkdocs-material && \
                                mkdocs build --strict
                            "
                        '''
                    }
                }
            }
        }

        stage('Security Scan') {
            parallel {
                stage('Backend - Trivy Image') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v /var/run/docker.sock:/var/run/docker.sock:Z \
                                aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 0 \
                                salonmaster-backend:latest || true
                        '''
                    }
                }

                stage('Docs - pip-audit') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Docs:/work:Z" -w /work python:3.12-alpine sh -c "
                                pip install --upgrade pip poetry pip-audit && \
                                poetry install --no-root && \
                                pip-audit
                            "
                        '''
                    }
                }

                stage('Kubernetes - pip-audit') {
                    steps {
                        sh '''
                            docker run -i --rm \
                                -v "$PWD/Kubernetes:/work:Z" -w /work python:3.12-alpine sh -s <<'HEREDOC_END'
pip install --upgrade pip poetry pip-audit
poetry install --no-root --with dev
pip-audit
HEREDOC_END
                        '''
                    }
                }

                stage('Website - Composer Audit') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v "$PWD/Website:/app:Z" -w /app composer:2 sh -c "
                                composer install --no-interaction --prefer-dist && \
                                composer audit || true
                            "
                        '''
                    }
                }
            }
        }

        stage('Publish') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'harbor-registry',
                    usernameVariable: 'HARBOR_USER',
                    passwordVariable: 'HARBOR_PASS'
                )]) {
                    sh '''
                        echo "$HARBOR_PASS" | docker login "$HARBOR_REGISTRY" -u "$HARBOR_USER" --password-stdin

                        docker tag salonmaster-backend "$HARBOR_REGISTRY/$HARBOR_PROJECT/backend:$BUILD_NUMBER"
                        docker tag salonmaster-backend "$HARBOR_REGISTRY/$HARBOR_PROJECT/backend:latest"
                        docker push "$HARBOR_REGISTRY/$HARBOR_PROJECT/backend:$BUILD_NUMBER"
                        docker push "$HARBOR_REGISTRY/$HARBOR_PROJECT/backend:latest"

                        docker tag salonmaster-website "$HARBOR_REGISTRY/$HARBOR_PROJECT/website:$BUILD_NUMBER"
                        docker tag salonmaster-website "$HARBOR_REGISTRY/$HARBOR_PROJECT/website:latest"
                        docker push "$HARBOR_REGISTRY/$HARBOR_PROJECT/website:$BUILD_NUMBER"
                        docker push "$HARBOR_REGISTRY/$HARBOR_PROJECT/website:latest"

                        docker logout "$HARBOR_REGISTRY"
                        echo "Published backend:$BUILD_NUMBER and website:$BUILD_NUMBER to Harbor"
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
