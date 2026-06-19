# Stage 1: Build frontend assets
FROM alpine:3.21 AS builder
RUN apk add --no-cache nodejs npm

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false
COPY . .
RUN npx mix --production 2>/dev/null || npm run build 2>/dev/null || true
RUN rm -rf node_modules
RUN mkdir -p public/build && touch public/mix-manifest.json

# Stage 2: Install PHP dependencies
FROM composer:2 AS composer
WORKDIR /app
COPY . .
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Stage 3: Production runtime
FROM alpine:3.21

RUN adduser -D -g 'www' www

RUN apk add --no-cache \
    supervisor nginx \
    php84 php84-fpm php84-dom php84-xml php84-pcntl php84-iconv \
    php84-session php84-openssl php84-mbstring php84-fileinfo \
    php84-tokenizer php84-xmlwriter php84-pdo php84-pdo_pgsql \
    php84-pecl-redis php84-ctype php84-curl php84-phar

RUN ln -sf /usr/bin/php84 /usr/bin/php

WORKDIR /www

COPY --from=builder /app /www
COPY --from=composer /app/vendor /www/vendor

COPY docker/website/www.conf /etc/php84/php-fpm.d/www.conf
COPY docker/website/nginx.conf /etc/nginx/nginx.conf
COPY docker/website/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN if [ -f /www/docker/website/php-log.ini ]; then \
        cp /www/docker/website/php-log.ini /etc/php84/php-fpm.d/php-log.conf; \
    fi

RUN rm -rf /www/docker /www/.git /www/node_modules 2>/dev/null || true

RUN php artisan event:cache 2>/dev/null || true; \
    php artisan route:cache 2>/dev/null || true; \
    php artisan view:cache 2>/dev/null || true; \
    php artisan config:cache 2>/dev/null || true; \
    chown -R www:www /www/storage /www/bootstrap/cache

EXPOSE 8080
USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
