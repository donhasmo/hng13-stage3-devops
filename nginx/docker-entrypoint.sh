#!/bin/sh
set -eu

# fallback
PORT=${PORT:-3000}

while true; do
    # Determine primary/backup based on ACTIVE_POOL
    if [ "${ACTIVE_POOL:-}" = "green" ]; then
      PRIMARY_NAME=app_green
      BACKUP_NAME=app_blue
    else
      PRIMARY_NAME=app_blue
      BACKUP_NAME=app_green
    fi

    export PRIMARY_NAME BACKUP_NAME PORT

    # Render nginx.conf
    envsubst '$PRIMARY_NAME $BACKUP_NAME $PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

    # Start nginx if not already running
    if ! pgrep nginx > /dev/null; then
        nginx -g "daemon off;" &
    else
        nginx -s reload
    fi

    # Watch ACTIVE_POOL changes every 2s
    sleep 1
done

