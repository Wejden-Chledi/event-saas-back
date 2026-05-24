# Dockerfile 
FROM python:3.11-slim
# Empêche Python de créer des fichiers .pyc et assure un log en temps réel
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
# Installation des outils nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    sed \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copie tout le contenu du projet, y compris entrypoint.sh qui est à la racine
COPY . .
# Rendre l'entrypoint exécutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Nettoyage des retours chariot Windows (\r) et droits d'exécution
# On cible le fichier qui a été copié dans /app/entrypoint.sh (puisque COPY . . a tout déplacé)
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh
EXPOSE 8000
# Utiliser l'entrypoint au lieu du CMD direct
ENTRYPOINT ["/entrypoint.sh"]
# Le fichier étant copié dans /app, il est maintenant à /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]