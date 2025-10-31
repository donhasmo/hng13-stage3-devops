import os
import json
import time
import requests
from collections import deque
from datetime import datetime

# ===========================================
# CONFIGURATION
# ===========================================
LOG_FILE = "/var/log/nginx/access.json.log"

# Read environment variables (with defaults)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
ERROR_THRESHOLD = float(os.getenv("ERROR_THRESHOLD", 5))
ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", 60))
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

# Rolling window to store recent logs (last N seconds)
WINDOW_SIZE = 10
log_window = deque(maxlen=WINDOW_SIZE)

last_alert_time = 0
last_pool = None

# ===========================================
# FUNCTION: Send message to Slack
# ===========================================
def send_slack_alert(message):
    global last_alert_time
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set, skipping alert.")
        return

    # Respect cooldown
    now = time.time()
    if now - last_alert_time < ALERT_COOLDOWN:
        print("In cooldown, skipping alert.")
        return

    data = {"text": f":rotating_light: {message}"}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=data)
        print(f"Alert sent: {message}")
        last_alert_time = now
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")

# ===========================================
# FUNCTION: Analyze recent logs
# ===========================================
def analyze_logs():
    if MAINTENANCE_MODE:
        print("Maintenance mode enabled. Skipping analysis.")
        return

    total = len(log_window)
    if total == 0:
        return

    errors = [log for log in log_window if log.get("status", "").startswith("5")]
    error_rate = (len(errors) / total) * 100

    if error_rate > ERROR_THRESHOLD:
        send_slack_alert(f"High 5xx error rate detected! ({error_rate:.1f}% in last {WINDOW_SIZE}s)")

# ===========================================
# FUNCTION: Detect Pool Flip
# ===========================================
def detect_pool_flip(current_pool):
    global last_pool
    if last_pool is None:
        last_pool = current_pool
    elif current_pool != last_pool:
        send_slack_alert(f"Nginx switched pool from {last_pool} → {current_pool}")
        last_pool = current_pool

# ===========================================
# MAIN LOOP: Tail log file and monitor
# ===========================================
def follow(file):
    file.seek(0, 2)  # move to end of file
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line

def main():
    print("Starting alert watcher...")
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        return

    with open(LOG_FILE, "r") as f:
        log_lines = follow(f)
        for line in log_lines:
            try:
                data = json.loads(line.strip())
                log_window.append(data)

                # Extract status and x_app_pool
                status = str(data.get("status", ""))
                current_pool = data.get("x_app_pool", "")

                # Detect pool changes
                if current_pool:
                    detect_pool_flip(current_pool)

                # Analyze error rate periodically
                if len(log_window) == log_window.maxlen:
                    analyze_logs()

            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    main()
