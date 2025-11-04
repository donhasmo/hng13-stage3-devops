import json
import time
from collections import deque

LOG_FILE = "/var/log/nginx/access.json.log"
WINDOW_SIZE = 200              # Number of recent requests to analyze
ERROR_RATE_THRESHOLD = 0.02    # 2%

def is_5xx(status):
    try:
        code = int(status)
        return 500 <= code < 600
    except:
        return False

def monitor_log():
    print(f"🚀 Alert Watcher started — monitoring {LOG_FILE}")
    recent_requests = deque(maxlen=WINDOW_SIZE)

    with open(LOG_FILE, "r") as log:
        # Seek to end of file to only watch new logs
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
                    # Calculate 5xx error rate
                    total_5xx = sum(1 for r in recent_requests if r["is_5xx"])
                    error_rate = total_5xx / WINDOW_SIZE

                    print(f"[STATS] Last {WINDOW_SIZE} requests: {total_5xx} were 5xx ({error_rate*100:.2f}%)")

                    if error_rate > ERROR_RATE_THRESHOLD:
                        print(f"[ALERT] High 5xx error rate ({error_rate*100:.2f}%) detected on *{pool}*")
                        # You could then trigger the redeploy/flip here
            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    monitor_log()

