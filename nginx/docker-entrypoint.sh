#!/bin/sh
set -e

# Decide primary/backup based on ACTIVE_POOL
if [ "$ACTIVE_POOL" = "blue" ]; then
    export PRIMARY_NAME=app_blue
    export BACKUP_NAME=app_green
else
    export PRIMARY_NAME=app_green
    export BACKUP_NAME=app_blue
fi

# Generate nginx.conf from template
envsubst '${PRIMARY_NAME} ${BACKUP_NAME} ${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "Starting nginx with PRIMARY=${PRIMARY_NAME}, BACKUP=${BACKUP_NAME} (active=${ACTIVE_POOL})"
nginx -g 'daemon off;'

