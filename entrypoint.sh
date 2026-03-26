#!/bin/sh

echo "Attente de la base de données..."

# attendre MySQL (adapter host/port)
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Base de données prête !"

echo "Application des migrations..."
python manage.py migrate --noinput

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Démarrage de Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000