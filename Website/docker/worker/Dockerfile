# Stage 1: Build application
FROM alpine AS builder
RUN apk add --update --no-cache \
    nodejs \
    npm \
    git \
    composer \
    php84 \
    php84-dom \
    php84-xml \
    php84-pcntl \
    php84-session \
    php84-fileinfo \
    php84-tokenizer \
    php84-xmlwriter

# Create a directory to hold your service and relevant modules with owner being node and define the working directory of your Docker container.
RUN mkdir -p /www/
WORKDIR /www

# Let us copy our package file into the working directory to make it the root directory from which we will install our dependency packages.
COPY . /www/

# Since we are all good let us, install our dependencies
RUN composer install --optimize-autoloader --no-dev
RUN php artisan clear-compiled

# Copy our project into our working container and initiate build
RUN rm -rf node_modules
RUN rm -rf docker

# Prepare runtime image
FROM alpine

# Create users
RUN adduser -D -g 'www' www

# Install dependencies
RUN apk add --update --no-cache \
    postfix \
    supervisor \
    php84 \
    php84-dom \
    php84-xml \
    php84-pgsql \
    php84-pcntl \
    php84-iconv \
    php84-session \
    php84-openssl \
    php84-mbstring \
    php84-fileinfo \
    php84-tokenizer \
    php84-xmlwriter \
    php84-pdo_pgsql \
    php84-pecl-redis

# Copy files and set permissions
RUN ln -sf /usr/bin/php84 /usr/bin/php
COPY --from=builder --chown=www /www /www
COPY docker/worker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/worker/transip.cf /etc/postfix/main.cf
COPY --chmod=0755 docker/worker/start-postfix.sh /usr/bin/start-postfix.sh

# Setup Laravel
WORKDIR /www
RUN php artisan event:cache
RUN php artisan route:cache
RUN php artisan view:cache

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
