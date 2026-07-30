
http:
  routers:

    dashboard-http:
      rule: Host(`${TRAEFIK_HOST}.${HOMELAB_DOMAIN}`)
      entryPoints:
        - websecure

      middlewares:
        - redirect-to-https

      service: api@internal

    dashboard-https:
      rule: Host(`${TRAEFIK_HOST}.${HOMELAB_DOMAIN}`)
      entryPoints:
        - websecure

      tls:
        certResolver: stepca

      middlewares:
        - dashboard-auth

      service: api@internal


  middlewares:

    redirect-to-https:

      redirectScheme:
        scheme: https
        permanent: true

    dashboard-auth:
      basicAuth:
        users:
          - "${TRAEFIK_BASIC_AUTH}"