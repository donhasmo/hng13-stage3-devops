# hng13-stage3-devops
DevOps Intern Stage 3 Task → Observability &amp; Alerts for Blue/Green (Log-Watcher + Slack)

## Stage 3 — Observability & Slack Alerts

### 1. Prepare
- Copy `.env.example` to `.env` and set `SLACK_WEBHOOK_URL` to your Slack incoming webhook URL.
- Optionally set `MAINTENANCE_MODE=true` while configuring.

### 2. Start services
docker-compose up -d --build

- Nginx will write structured JSON logs to the shared volume `nginx_logs`.
- The `alert_watcher` service will tail `/var/log/nginx/access.json.log` and post alerts.
  docker exec -it alert_watcher bash
  cat /var/log/nginx/access.json.log


### 2.1 Confirm app
curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

### 3. Simulate failover to green_app with high error rate
- Make Enough request for logs to reach window size:
  for i in {1..50}; do
    curl -s http://localhost:8080/version > /dev/null
  done
- Check alert_watcher logs:
  docker logs alert_watcher
- Stop the currently active app container to cause Nginx to start using the other pool:
  curl -X POST "http://localhost:8081/chaos/start?mode=error"
- Send Enough request for logs error threshold to reach:
  curl -s http://localhost:8080/version
- Check alert_watcher logs again:
  docker logs alert_watcher

### 3.1 Stop chaos and confirm failover
  curl -X POST "http://localhost:8081/chaos/stop"
- Check headers:
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

### 4. Revert back to blue_app
- Confirm running app(green_app should be running) :
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'
- Make enough request to make error lower than threshold by sending more success request:
  for i in {1..50}; do
    curl -s http://localhost:8080/version > /dev/null
  done
- Confirm revert(blue_app should be running) :
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

- Check alert_watcher logs again:
  docker logs alert_watcher

### 4.1 Stop chaos and confirm failover
- Wait for cooldown time to reach and trigger error on current app:
  curl -X POST "http://localhost:8082/chaos/stop"
- Check headers:
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

for i in {1..200}; do
    curl -s http://localhost:8080/version > /dev/null
  done
