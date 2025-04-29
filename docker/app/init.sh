#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
while ! nc -z 192.168.100.35 5432; do
  sleep 0.5
done
echo "PostgreSQL is accessible"

# Skip migrations for now to get the app running
export FLASK_APP=run.py

# Start the application
echo "Starting Flask application..."
exec "$@"
