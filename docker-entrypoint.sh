#!/bin/bash
set -e

echo "Starting Django application..."

# For Cloud SQL, we use Unix socket connections, so skip pg_isready check
# The DATABASE_URL is already configured for Unix socket via Cloud SQL proxy
# Cloud Run automatically sets up the /cloudsql directory with the socket

echo "Database connection configured via DATABASE_URL"
echo "Cloud SQL connection will use Unix socket in /cloudsql/"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table if needed (for future caching)
echo "Ensuring database tables are ready..."
python manage.py createcachetable 2>/dev/null || true

echo "Starting server..."
exec "$@"

