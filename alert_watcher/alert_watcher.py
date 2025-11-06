#!/usr/bin/env python3
import os
import json
import time
from collections import deque
import subprocess

# ==========================
# CONFIGURATION
# ==========================
LOG_FILE = "/var/log/nginx/access.json.log"
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 50))
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_THRESHOLD", 2)) / 100
FLIP_COOLDOWN_SECONDS = int(os.getenv("FLIP_COOLDOWN_SECONDS", 30))
MAINTENANCE_MODE_ENABLED = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
NGINX_CONF = "/etc/nginx/nginx.conf"

current_pool = "blue"
last_flip_time = 0  # Timestamp of last flip

POOL_MAP = {
    "blue": "app_blue",
    "green": "app_green"
}

# ==========================
# HELPER FUNCTIONS
# ==========================

def is_5xx(status):
    """Check if HTTP status code is a 5xx error."""
    try:
        code = int(status)
        return 500 <= code < 600
    except:
        return False

def enable_maintenance():
    """Enable maintenance mode by swapping index.html with maintenance.html."""
    print("[INFO] Enabling maintenance mode...")
    try:
        subprocess.run([
            "docker", "exec", "nginx_bluegreen", "sh", "-c",
            "cp /usr/share/nginx/html/maintenance.html /usr/share/nginx/html/index.html"
        ], check=True)
        print("[INFO] Maintenance mode enabled.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to enable maintenance mode: {e}")

def disable_maintenance():
    """Disable maintenance mode by restoring the original index.html."""
    print("[INFO] Disabling maintenance mode...")
    try:
        subprocess.run([
            "docker", "exec", "nginx_bluegreen", "sh", "-c",
            "cp /usr/share/nginx/html/backup_index.html /usr/share/nginx/html/index.html"
        ], check=True)
        print("[INFO] Maintenance mode disabled.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to disable maintenance mode: {e}")

def flip_pool_to(target_pool):
    """Switch Nginx to route traffic to the target pool."""
    global current_pool, last_flip_time
    now = time.time()

    if now - last_flip_time < FLIP_COOLDOWN_SECONDS:
        print(f"[INFO] Flip cooldown active — skipping flip to {target_pool}")
        return

    try:
        if MAINTENANCE_MODE_ENABLED:
            enable_maintenance()

        primary = POOL_MAP[target_pool]
        backup = POOL_MAP["green" if target_pool == "blue" else "blue"]

        subprocess.run([
            "docker", "exec", "nginx_bluegreen", "sh", "-c",
            f"sed -i 's/server .*:3000 max_fails=1 fail_timeout=5s;/server {primary}:3000 max_fails=1 fail_timeout=5s;/g' {NGINX_CONF} && "
            f"sed -i 's/server .*:3000 backup;/server {backup}:3000 backup;/g' {NGINX_CONF} && "
            f"nginx -s reload"
        ], check=True)

        print(f"[ACTION] Flipped pool to {target_pool}")
        current_pool = target_pool
        last_flip_time = now

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to flip pool: {e}")

    finally:
        if MAINTENANCE_MODE_ENABLED:
            disable_maintenance()

def monitor_log():
    """Continuously monitor Nginx access logs for 5xx errors."""
    print(f"Alert Watcher started — monitoring {LOG_FILE}")
    recent_requests = deque(maxlen=WINDOW_SIZE)
    global current_pool

    with open(LOG_FILE, "r") as log:
        log.seek(0, 2)
        while True:
            line = log.readline()
            if not line:
                time.sleep(1)
                continue

            try:
                entry = json.loads(line.strip())
                status = entry.get("status")
                pool = entry.get("x_app_pool", "unknown")

                recent_requests.append({
                    "status": status,
                    "pool": pool,
                    "is_5xx": is_5xx(status)
                })

                if len(recent_requests) >= WINDOW_SIZE:
                    total_5xx = sum(1 for r in recent_requests if r["is_5xx"])
                    error_rate = total_5xx / WINDOW_SIZE

                    print(f"[STATS] Last {WINDOW_SIZE} requests: {total_5xx} were 5xx ({error_rate*100:.2f}%)")

                    # Flip logic with cooldown
                    if error_rate > ERROR_RATE_THRESHOLD and current_pool == "blue":
                        print(f"[ALERT] High 5xx rate ({error_rate*100:.2f}%) — flipping to green")
                        flip_pool_to("green")
                    elif error_rate <= ERROR_RATE_THRESHOLD and current_pool == "green":
                        print(f"[INFO] Error rate normal ({error_rate*100:.2f}%) — flipping back to blue")
                        flip_pool_to("blue")

            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    monitor_log()
