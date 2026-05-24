#!/bin/sh

# Redirige toutes les sorties (stdout et stderr) vers les logs système
# Cela permet de voir les erreurs de crash dans les "Console Logs" Azure
exec > >(tee -a /proc/1/fd/1) 2>&1

echo "--- DÉMARRAGE DU ENTRYPOINT ---"

# Vérification de sécurité des variables
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
    echo "ERREUR : Les variables DB_HOST ou DB_PORT ne sont pas configurées dans Azure."
    exit 1
fi

echo "Attente de la base de données sur $DB_HOST:$DB_PORT..."

# Attendre que MySQL soit prêt
while ! nc -z -v -w 5 $DB_HOST $DB_PORT; do
  echo "La base de données n'est pas encore disponible... attente."
  sleep 2
done

echo "Base de données prête !"

# Application des migrations
echo "Application des migrations..."
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "ERREUR : La migration a échoué."
    exit 1
fi

# Collecte des fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrage de l'application
echo "Démarrage de Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000