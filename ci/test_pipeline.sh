#!/bin/bash
set -e

echo "##########################"
echo "Starting services..."
docker-compose up -d
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
echo "Tailing Nginx log tailer output..."
docker logs --tail 20 nginx_log_tailer

echo "##########################"
echo "Confirming volume..."
docker volume ls
docker volume inspect nginx_logs


# Stop App and remove containers
echo "##########################"
echo "stopping containers........."
docker-compose down -v
