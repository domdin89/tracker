#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL || true
fi

# Start server
echo "Starting server..."
if [ "$DEBUG" = "True" ]; then
    echo "Running in DEBUG mode..."
    python manage.py runserver 0.0.0.0:80
else
    echo "Running in PRODUCTION mode..."
    gunicorn tracker.wsgi:application \
        --bind 0.0.0.0:80 \
        --workers 4 \
        --timeout 600 \
        --error-logfile /app/logs/error.log \
        --access-logfile /app/logs/access.log \
        --capture-output \
        --log-level info
fi