FROM caddy:2.11.4-alpine

# The official image prepares /data/caddy and /config/caddy as writable
# locations. Run the public edge as an unprivileged numeric user; Compose grants
# only NET_BIND_SERVICE so Caddy can listen on 80/443.
USER 10001:10001
