#!/bin/sh

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Gather topology data
python manage.py gather_topology

# Collect static files
python manage.py collectstatic --noinput

# Create a superuser (optional, remove if not needed)
# echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')" | python manage.py shell

# Start the Django development server
python manage.py runserver 0.0.0.0:8000
