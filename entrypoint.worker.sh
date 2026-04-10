#!/bin/sh

echo "Attente de la base de données..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Démarrage Celery Worker..."

celery -A config worker -l info