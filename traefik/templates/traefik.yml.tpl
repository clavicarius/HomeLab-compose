api:
  dashboard: true
  debug: false


log:
  level: INFO


entryPoints:

  web:
    address: ":80"

  websecure:
    address: ":443"


providers:

  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false

  file:
    filename: /etc/traefik/dynamic.yml
    watch: true


certificatesResolvers:
  stepca:
    acme:
      email: admin@${HOMELAB_DOMAIN}
      caServer: https://step-ca.${HOMELAB_DOMAIN}/acme/acme/directory
      storage: /data/acme.json
