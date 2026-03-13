FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système pour mysqlclient + build essentials
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

EXPOSE 8000
CMD ["gunicorn", "event-saas-back.wsgi:application", "--bind", "0.0.0.0:8000"]