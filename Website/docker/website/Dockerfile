# Stage 1: Build application
FROM alpine:latest AS builder
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
    php84-mbstring \
    php84-xmlwriter

# Create a directory to hold your service and relevant modules with owner being node and define the working directory of your Docker container.
RUN mkdir -p /www/
WORKDIR /www

# Let us copy our package file into the working directory to make it the root directory from which we will install our dependency packages.
COPY . /www/

# Since we are all good let us, install our dependencies
RUN npm install
RUN php --version
RUN composer install --optimize-autoloader --no-dev
RUN php artisan clear-compiled

# Copy our project into our working container and initiate build
RUN npx mix --production
RUN rm -rf node_modules
RUN rm -rf docker

# Prepare runtime image
FROM alpine

# Create users
RUN adduser -D -g 'www' www

# Install dependencies
RUN apk add --update --no-cache \
    supervisor \
    nmap \
    nginx \
    php84 \
    php84 \
    php84-fpm \
    php84-dom \
    php84-xml \
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
COPY docker/website/www.conf /etc/php84/php-fpm.d/www.conf
COPY docker/website/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/website/php-log.ini /etc/php84/php-fpm.d/php-log.conf

# Setup Laravel
WORKDIR /www
RUN php artisan event:cache
RUN php artisan route:cache
RUN php artisan view:cache

USER root
EXPOSE 8080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
