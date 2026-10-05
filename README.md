# Event SaaS Platform — Backend

Backend de la plateforme **Event SaaS**, une application SaaS intelligente de gestion d'événements développée avec Django et Django REST Framework.

Le backend fournit une API REST permettant de gérer les utilisateurs, organisations, événements, inscriptions, paiements, notifications, feedbacks et fonctionnalités basées sur l'intelligence artificielle.

## 📋 Présentation

Event SaaS permet aux organisations de créer et gérer leurs événements, de suivre les inscriptions et les participants, et d'analyser les performances des événements.

Les participants peuvent explorer les événements, s'inscrire, effectuer des paiements et recevoir leurs billets avec QR code.

Le backend intègre également des fonctionnalités IA pour assister les gestionnaires et analyser les feedbacks des participants.

## ✨ Fonctionnalités principales

### 👥 Gestion des utilisateurs

* Authentification avec JWT
* Gestion des rôles et permissions
* Propriétaire, gestionnaire, staff et participant
* Gestion des organisations et des membres

### 📅 Gestion des événements

* Création et modification des événements
* Publication et gestion du statut des événements
* Gestion des capacités et inscriptions
* Gestion des images et médias
* Génération de descriptions avec l'IA

### 🎫 Inscriptions et billets

* Inscription aux événements
* Gestion des participants
* Génération de billets
* Génération de QR codes
* Validation des billets par le staff

### 💳 Paiements

* Intégration Stripe
* Gestion des paiements pour les événements payants
* Gestion des confirmations de paiement
* Webhooks Stripe

### 🤖 Intelligence artificielle

* Assistant IA
* Génération de descriptions d'événements
* Suggestions et recommandations
* Analyse des feedbacks
* Analyse de sentiment
* Génération de rapports

### 🔔 Notifications

* Notifications liées aux événements
* Notifications aux participants
* Tâches automatisées avec Celery

## 🛠️ Technologies utilisées

| Technologie           | Utilisation                   |
| --------------------- | ----------------------------- |
| Python 3.11+          | Langage principal             |
| Django 5.2            | Framework backend             |
| Django REST Framework | API REST                      |
| Simple JWT            | Authentification JWT          |
| MySQL                 | Base de données               |
| Azure MySQL           | Base de données en production |
| Azure Blob Storage    | Stockage des médias           |
| Azure OpenAI          | Fonctionnalités IA            |
| Redis                 | Cache et broker               |
| Celery                | Tâches asynchrones            |
| Stripe                | Paiements                     |
| Docker                | Conteneurisation              |
| Swagger / OpenAPI     | Documentation API             |
| Pytest / Django Tests | Tests                         |

## 🏗️ Architecture

```text
event-saas-back/
│
├── apps/
│   ├── users/             # Utilisateurs et authentification
│   ├── organisations/     # Organisations et rôles
│   ├── events/            # Gestion des événements et IA
│   ├── inscriptions/      # Inscriptions et billets
│   ├── payments/          # Paiements Stripe
│   ├── notifications/     # Notifications
│   ├── assistant/         # Assistant IA
│   └── feedback/          # Feedback et analyse
│
├── config/
│   ├── settings/
│   │   ├── base.py        # Configuration commune
│   │   ├── dev.py         # Développement
│   │   ├── prod.py        # Production
│   │   └── test.py        # Tests
│   │
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # WSGI
│   └── asgi.py            # ASGI
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── azure-pipelines.yml
├── .gitignore
└── README.md
```

## 📋 Prérequis

Avant de commencer, installer :

* Python 3.11 ou supérieur
* MySQL 8.0 ou supérieur
* Git
* Redis
* Node.js 20+ si vous souhaitez utiliser le frontend
* Docker (optionnel)

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd Event-SaaS/event-saas-back
```

### 2. Créer l'environnement virtuel

#### Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 🔐 Configuration de l'environnement

Le projet utilise des variables d'environnement pour les informations sensibles.

Créer un fichier `.env` dans `event-saas-back/`.

**Ne jamais publier ce fichier sur GitHub.**

Exemple :

```env
# Django
SECRET_KEY=your_django_secret_key
DJANGO_ENV=development
ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DB_NAME=event_saas
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=your_mysql_host
DB_PORT=3306
MYSQL_ATTR_SSL_CA=DigiCertGlobalRootG2.crt.pem

# Stripe
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key

# Azure Storage
AZURE_ACCOUNT_NAME=your_storage_account
AZURE_ACCOUNT_KEY=your_storage_key
AZURE_CONTAINER=event-media

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Pour un dépôt public, les vraies valeurs doivent rester uniquement dans les variables d'environnement.

## 🗄️ Base de données

Le projet utilise MySQL.

Après avoir configuré les variables d'environnement :

```bash
python manage.py makemigrations
python manage.py migrate
```

Pour vérifier les migrations :

```bash
python manage.py showmigrations
```

## 👤 Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivre ensuite les instructions affichées dans le terminal.

## ▶️ Démarrer le serveur

```bash
python manage.py runserver
```

Le backend sera disponible sur :

```text
http://127.0.0.1:8000/
```

## 📚 API

### Documentation Swagger / OpenAPI

```text
http://127.0.0.1:8000/api/docs/
```

### Administration Django

```text
http://127.0.0.1:8000/admin/
```

### Health Check

```text
http://127.0.0.1:8000/health/
```

## 🔑 Authentification

L'API utilise une authentification JWT.

Les utilisateurs obtiennent un access token et un refresh token après authentification.

Exemple :

```http
Authorization: Bearer <access_token>
```

Le système permet également le renouvellement automatique des tokens.

## 🤖 Fonctionnalités IA

Le backend utilise Azure OpenAI pour certaines fonctionnalités intelligentes.

### Assistant IA

L'assistant peut aider les utilisateurs dans différentes opérations liées aux événements.

### Génération de descriptions

Le gestionnaire peut générer automatiquement une description d'événement à partir de plusieurs informations :

* titre
* lieu
* capacité
* prix
* catégorie
* autres informations disponibles

### Analyse des feedbacks

Les feedbacks des participants peuvent être analysés afin d'obtenir :

* sentiment général
* statistiques
* tendances
* rapports d'analyse

Ces fonctionnalités permettent aux organisateurs de mieux comprendre l'expérience des participants.

## 💳 Stripe

Les paiements sont gérés avec Stripe.

Les clés Stripe doivent être configurées dans `.env` :

```env
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
```

**La clé secrète Stripe ne doit jamais être publiée sur GitHub.**

Pour les tests, utiliser uniquement les cartes de test fournies par Stripe.

## ⚙️ Tâches asynchrones

Le projet utilise :

* Redis
* Celery

pour exécuter certaines tâches en arrière-plan.

Exemple :

```bash
celery -A config worker --loglevel=info
```

Selon la configuration du projet, Celery Beat peut également être utilisé pour les tâches planifiées.

## 🧪 Tests

Exécuter tous les tests :

```bash
python manage.py test
```

Exécuter les tests d'une application :

```bash
python manage.py test apps.events
```

Vérifier la configuration Django :

```bash
python manage.py check
```

## 🐳 Docker

Construire l'image :

```bash
docker build -t event-saas-back .
```

Lancer le conteneur :

```bash
docker run -p 8000:8000 event-saas-back
```

Les variables d'environnement nécessaires doivent être configurées lors du déploiement.

## ☁️ Déploiement Azure

Le backend peut être déployé sur Azure avec une architecture basée sur :

* Azure Container Registry
* Azure Container Apps / App Service
* Azure MySQL
* Azure Blob Storage
* Azure OpenAI
* Redis
* Azure DevOps pour le CI/CD

Les informations sensibles doivent être configurées dans les variables d'environnement ou les paramètres sécurisés du service Azure.

## 🔒 Sécurité

Le projet utilise notamment :

* JWT
* CORS
* HTTPS en production
* SSL pour la connexion MySQL
* variables d'environnement pour les secrets
* permissions selon les rôles
* validation des données API

Les fichiers suivants ne doivent jamais être publiés :

```text
.env
.env.*
.venv/
__pycache__/
*.pyc
```

## 🔗 Frontend

Le frontend React est disponible dans :

```text
../event-saas-front/
```

Pour installer et démarrer le frontend :

```bash
cd ../event-saas-front
npm install
npm run dev
```

Le frontend sera disponible sur :

```text
http://localhost:5173/
```

## 🤝 Contribution

1. Créer une branche :

```bash
git checkout -b feature/nouvelle-fonctionnalite
```

2. Développer la fonctionnalité.

3. Ajouter les tests nécessaires.

4. Vérifier le projet :

```bash
python manage.py check
python manage.py test
```

5. Commit :

```bash
git commit -m "Add: nouvelle fonctionnalité"
```

6. Push :

```bash
git push origin feature/nouvelle-fonctionnalite
```

7. Créer une Pull Request.

## 📄 Licence

Ce projet est distribué sous licence MIT.

---

**Event SaaS — Plateforme intelligente de gestion d'événements**

Technologies principales : **Django · DRF · MySQL · Azure · Stripe · Redis · Celery · Azure OpenAI**
