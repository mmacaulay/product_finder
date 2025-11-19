#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for database to be ready (with timeout)
echo "Waiting for database..."
timeout=30
counter=0
until pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" 2>/dev/null || [ $counter -eq $timeout ]; do
  counter=$((counter+1))
  echo "Database is unavailable - waiting... ($counter/$timeout)"
  sleep 1
done

if [ $counter -eq $timeout ]; then
  echo "Warning: Database connection timeout. Proceeding anyway..."
fi

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

