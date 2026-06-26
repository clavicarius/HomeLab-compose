FROM php:5.6-apache

# Fix für alte Debian Jessie Repositories
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list \
 && sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list \
 && sed -i '/stretch-updates/d' /etc/apt/sources.list \
 && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99jessie \
 && echo 'Acquire::AllowInsecureRepositories "true";' >> /etc/apt/apt.conf.d/99jessie \
 && echo 'APT::Get::AllowUnauthenticated "true";' >> /etc/apt/apt.conf.d/99jessie \
 && apt-get -o Acquire::Check-Valid-Until=false \
            -o Acquire::AllowInsecureRepositories=true \
            update

# Systempakete
RUN apt-get install -y --allow-unauthenticated \
    libpng-dev \
    libicu-dev \
    libjpeg-dev \
    libfreetype6-dev \
    git \
    unzip

# GD für PHP 5.6 konfigurieren
RUN docker-php-ext-configure gd \
    --with-freetype-dir=/usr/include/ \
    --with-jpeg-dir=/usr/include/

# PHP Extensions
RUN docker-php-ext-install \
    mysqli \
    pdo \
    pdo_mysql \
    gd \
    intl \
    mbstring

# Letzte kompatible Xdebug-Version für PHP 5.6
RUN pecl install xdebug-2.5.5 \
 && docker-php-ext-enable xdebug

# Composer (PHP 5.6 kompatibel)
COPY --from=composer:1 /usr/bin/composer /usr/bin/composer

# Apache Module
RUN a2enmod rewrite
