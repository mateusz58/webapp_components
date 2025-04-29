#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
while ! nc -z 192.168.100.35 5432; do
  sleep 0.5
done
echo "PostgreSQL is accessible"

# Set Flask configuration
export FLASK_APP=run.py

# Do not run migrations automatically to avoid permission issues
# Instead, we'll need to run them manually as a superuser

# Start the application
echo "Starting Flask application..."
exec "$@"
