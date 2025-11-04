# hng13-stage3-devops
DevOps Intern Stage 3 Task → Observability &amp; Alerts for Blue/Green (Log-Watcher + Slack)

## Stage 3 — Observability & Slack Alerts

### 1. Prepare
- Copy `.env.example` to `.env` and set `SLACK_WEBHOOK_URL` to your Slack incoming webhook URL.
- Optionally set `MAINTENANCE_MODE=true` while configuring.

### 2. Start services
docker-compose --env-file .env up -d

- Nginx will write structured JSON logs to the shared volume `nginx_logs`.
- The `alert_watcher` service will tail `/var/log/nginx/access.json.log` and post alerts.
  docker exec -it alert_watcher bash
  cat /var/log/nginx/access.json.log


### 2.1 Confirm app
curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

### 3. Simulate failover
- Stop the currently active app container to cause Nginx to start using the other pool:
  curl -X POST "http://localhost:8081/chaos/start?mode=error"
- You should see a Slack alert like "Failover detected: BLUE → GREEN".
- Check the headers to confirm failover:
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

### 3.1 Stop chaos
  curl -X POST "http://localhost:8081/chaos/stop"
- Check headers:
  curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

### 4. Simulate high error rate
- Produce 5xx responses from the active upstream
- Once the 5xx rate over the window exceeds ERROR_RATE_THRESHOLD, the watcher posts an error-rate alert.
  for i in {1..10}; do \
  docker exec nginx_bluegreen sh -c 'echo "{\"status\":500,\"x_app_pool\":\"blue\"}" >> /var/log/nginx/access.json.log'; \
done

### 5. Inspect logs
- Nginx logs (sample line): `docker-compose exec nginx cat /var/log/nginx/access.json | jq .`
- Watch the `alert_watcher` logs:
  docker-compose logs -f alert_watcher

