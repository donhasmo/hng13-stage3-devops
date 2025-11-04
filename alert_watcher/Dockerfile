FROM python:3.10-slim

WORKDIR /app

COPY alert_watcher.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 👇 install docker-cli so subprocess.run(["docker", ...]) works
RUN apt-get update && apt-get install -y docker-cli && rm -rf /var/lib/apt/lists/*

CMD ["python", "-u", "alert_watcher.py"]
