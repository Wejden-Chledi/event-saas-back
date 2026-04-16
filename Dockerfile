# Dockerfile 
FROM python:3.11-slim

# Empêche Python de créer des fichiers .pyc et assure un log en temps réel
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rendre l'entrypoint exécutable
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh


EXPOSE 8000

# Utiliser l'entrypoint au lieu du CMD direct
ENTRYPOINT ["/entrypoint.sh"]