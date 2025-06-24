FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including davfs2 for WebDAV mounting
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    davfs2 \
    fuse \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the initialization script executable
COPY docker/app/init.sh /init.sh
RUN chmod +x /init.sh

# Expose port 6002 instead of 5000
EXPOSE 6002

# Use the initialization script as entrypoint
ENTRYPOINT ["/init.sh"]

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=6002"]
