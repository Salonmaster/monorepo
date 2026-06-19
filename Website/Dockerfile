# Stage 1: Build frontend assets
FROM alpine:3.21 AS builder
RUN apk add --no-cache nodejs npm

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false
COPY . .
RUN npx mix --production 2>/dev/null || npm run build 2>/dev/null || true
RUN rm -rf node_modules
# Ensure public/ exists even if frontend build skipped
RUN mkdir -p public/build && touch public/mix-manifest.json

# Stage 2: Production runtime
FROM alpine:3.21

RUN adduser -D -g 'www' www

RUN apk add --no-cache \
    supervisor nginx \
    php82 php82-fpm php82-dom php82-xml php82-pcntl php82-iconv \
    php82-session php82-openssl php82-mbstring php82-fileinfo \
    php82-tokenizer php82-xmlwriter php82-pdo php82-pdo_pgsql \
    php82-pecl-redis php82-ctype php82-curl php82-phar

RUN ln -sf /usr/bin/php82 /usr/bin/php

WORKDIR /www

# Copy everything from builder (code + built assets)
COPY --from=builder /app /www

# Install production PHP deps
# apk composer pulls php83, but runtime uses php82 — add php83 extensions for build scripts
RUN apk add --no-cache composer php83-dom php83-session php83-fileinfo php83-tokenizer && \
    composer install --no-dev --optimize-autoloader --no-interaction && \
    apk del composer

# Copy configs
COPY docker/website/www.conf /etc/php82/php-fpm.d/www.conf
COPY docker/website/nginx.conf /etc/nginx/nginx.conf
COPY docker/website/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy php-log.ini if it exists
RUN if [ -f /www/docker/website/php-log.ini ]; then \
        cp /www/docker/website/php-log.ini /etc/php82/php-fpm.d/php-log.conf; \
    fi

# Remove docker dir from final image
RUN rm -rf /www/docker /www/.git /www/node_modules 2>/dev/null || true

# Setup Laravel
RUN php artisan event:cache 2>/dev/null || true; \
    php artisan route:cache 2>/dev/null || true; \
    php artisan view:cache 2>/dev/null || true; \
    php artisan config:cache 2>/dev/null || true; \
    chown -R www:www /www/storage /www/bootstrap/cache

EXPOSE 8080
USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
