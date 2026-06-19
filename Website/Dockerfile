# Stage 1: Build frontend assets
FROM alpine:3.21 AS builder
RUN apk add --no-cache nodejs npm

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false

COPY . .
RUN npx mix --production 2>/dev/null || npm run build 2>/dev/null || true
RUN rm -rf node_modules

# Stage 2: Production runtime
FROM alpine:3.21

RUN adduser -D -g 'www' www

RUN apk add --no-cache \
    supervisor \
    nginx \
    php82 \
    php82-fpm \
    php82-dom \
    php82-xml \
    php82-pcntl \
    php82-iconv \
    php82-session \
    php82-openssl \
    php82-mbstring \
    php82-fileinfo \
    php82-tokenizer \
    php82-xmlwriter \
    php82-pdo \
    php82-pdo_pgsql \
    php82-pecl-redis \
    php82-ctype \
    php82-curl \
    php82-phar

RUN ln -sf /usr/bin/php82 /usr/bin/php

WORKDIR /www

# Copy app code
COPY --chown=www composer.json composer.lock artisan ./
COPY --chown=www app/ app/
COPY --chown=www bootstrap/ bootstrap/
COPY --chown=www config/ config/
COPY --chown=www database/ database/
COPY --chown=www public/ public/
COPY --chown=www resources/ resources/
COPY --chown=www routes/ routes/
COPY --chown=www storage/ storage/

# Copy frontend build from builder stage
COPY --from=builder --chown=www /app/public/build public/build 2>/dev/null || true
COPY --from=builder --chown=www /app/public/mix-manifest.json public/ 2>/dev/null || true

# Install production PHP deps
RUN apk add --no-cache composer && \
    composer install --no-dev --optimize-autoloader --no-interaction && \
    apk del composer

# Copy configs
COPY docker/website/www.conf /etc/php82/php-fpm.d/www.conf
COPY docker/website/nginx.conf /etc/nginx/nginx.conf
COPY docker/website/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/website/php-log.ini /etc/php82/php-fpm.d/php-log.conf 2>/dev/null || true

# Setup Laravel
RUN php artisan event:cache 2>/dev/null || true && \
    php artisan route:cache 2>/dev/null || true && \
    php artisan view:cache 2>/dev/null || true && \
    php artisan config:cache 2>/dev/null || true && \
    chown -R www:www /www/storage /www/bootstrap/cache

EXPOSE 8080
USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
