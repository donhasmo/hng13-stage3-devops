#!/bin/sh
set -eu

# default PORT fallback
PORT=${PORT:-3000}

# Determine primary/backup service names based on ACTIVE_POOL
if [ "${ACTIVE_POOL:-}" = "green" ]; then
  PRIMARY_NAME=app_green
  BACKUP_NAME=app_blue
else
  PRIMARY_NAME=app_blue
  BACKUP_NAME=app_green
fi

export PRIMARY_NAME BACKUP_NAME PORT

# Render the template into actual nginx.conf
envsubst '$PRIMARY_NAME $BACKUP_NAME $PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start nginx in foreground so docker container stays alive
nginx -g "daemon off;"
