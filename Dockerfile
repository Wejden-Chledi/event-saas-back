# Dockerfile corrigé pour Azure
FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour mysqlclient et compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Commande par défaut pour Azure Container Apps
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]