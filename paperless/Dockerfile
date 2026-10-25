FROM paperlessngx/paperless-ngx:3.3

USER root
RUN apt-get update \
    && apt-get install --no-install-recommends --yes libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*
