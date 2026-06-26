FROM php:8.5-apache

RUN apt-get update && apt-get install -y \
    libpng-dev \
    libicu-dev \
    libonig-dev \
    libzip-dev \
    unzip \
    git \
    && docker-php-ext-install mysqli pdo pdo_mysql gd intl mbstring

RUN pecl install xdebug \
    && docker-php-ext-enable xdebug

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
