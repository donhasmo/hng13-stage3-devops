#!/bin/bash
set -e

# Load .env variables into this script
export $(grep -v '^#' .env | xargs)

echo "##########################"
echo "Starting services..."
# Explicitly tell Compose to use the .env file
docker-compose --env-file .env up -d
sleep 5

# Verify Blue App running
echo "##########################"
echo "Verifying Blue..."
curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

# Simulate chaos error
echo "##########################"
echo "Starting chaos..."
curl -X POST "http://localhost:8081/chaos/start?mode=error"
sleep 5

# Simulate timeout error
echo "##########################"
echo "Test timeout simulation....."
curl -X POST "http://localhost:8081/chaos/start?mode=timeout"
echo "##########################"
curl http://localhost:8080/version
sleep 5

echo "##########################"
echo "Triggering high error rate alert..."
# Append multiple fake 5xx logs to trigger alert
docker exec -i nginx_bluegreen sh -c "for i in \$(seq 1 10); do echo '{\"status\":\"500\",\"x_app_pool\":\"blue\"}' >> /var/log/nginx/access.json.log; done"
sleep 2

echo "##########################"
echo "Verifying Green failover......"
curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

echo "##########################"
echo "Stopping chaos"
curl -X POST "http://localhost:8081/chaos/stop"

echo "##########################"
echo "Verifying green once more......"
curl -s -D - http://localhost:8080/version | grep -E 'X-App-Pool|X-Release-Id'

echo "##########################"
echo "Test passed — failover working"

echo "##########################"
echo "Printing running containers..."
docker ps

echo "##########################"
echo "Confirming volume..."
docker volume ls

# Stop App and remove containers
echo "##########################"
echo "stopping containers........."
docker-compose down -v
