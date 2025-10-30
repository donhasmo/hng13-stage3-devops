# hng13-stage3-devops
DevOps Intern Stage 3 Task → Observability &amp; Alerts for Blue/Green (Log-Watcher + Slack)

## Stage 3 — Observability & Slack Alerts

### 1. Prepare
- Copy `.env.example` to `.env` and set `SLACK_WEBHOOK_URL` to your Slack incoming webhook URL.
- Optionally set `MAINTENANCE_MODE=true` while configuring.

### 2. Start services
docker-compose up -d --build

- Nginx will write structured JSON logs to the shared volume `nginx_logs`.
- The `alert_watcher` service will tail `/var/log/nginx/access.json` and post alerts.

### 3. Simulate failover
- Stop the currently active app container to cause Nginx to start using the other pool:
  docker-compose stop app_blue   # example
- You should see a Slack alert like "Failover detected: BLUE → GREEN".

### 4. Simulate high error rate
- Produce 5xx responses from the active upstream (e.g., temporarily modify the app to return 500 for some requests) and generate ~WINDOW_SIZE requests.
- Once the 5xx rate over the window exceeds ERROR_RATE_THRESHOLD, the watcher posts an error-rate alert.

### 5. Inspect logs
- Nginx logs (sample line): `docker-compose exec nginx cat /var/log/nginx/access.json | jq .`
- Watch the `alert_watcher` logs:
  docker-compose logs -f alert_watcher

