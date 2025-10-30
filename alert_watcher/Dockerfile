# Start from a lightweight Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy files into container
COPY alert_watcher.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Mount nginx logs inside container
VOLUME ["/var/log/nginx"]

# Run watcher
CMD ["python", "alert_watcher.py"]
