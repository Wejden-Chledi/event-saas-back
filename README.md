#  Event SaaS Platform

Une plateforme SaaS complète pour la gestion d'événements avec inscription simple, paiement Stripe et assistant IA.

## 📋 Vue d'Ensemble

Event SaaS est une application web moderne permettant aux organisations de créer, gérer et publier des événements. Les participants peuvent s'inscrire, payer et recevoir des billets QR code. La plateforme inclut un assistant IA pour aider à la création d'événements.

### 🎯 Fonctionnalités Principales

#### 🏢 Pour les Organisations
- **Gestion multi-rôles** : Propriétaires, gestionnaires, staff, participants
- **Création d'événements** : Interface complète avec formulaire intelligent
- **Assistant IA** : Génération automatique de descriptions d'événements
- **Gestion des inscriptions** : Suivi en temps réel des participants
- **Analytics** : Statistiques et graphiques sur les événements
- **Notifications** : Système de notifications en temps réel

#### 🎫 Pour les Participants
- **Exploration d'événements** : Catalogue avec recherche et filtres
- **Inscription simple** : Processus en 1-clic avec vérification des places
- **Paiement sécurisé** : Intégration Stripe complète
- **Billets QR code** : Génération et validation automatique
- **Dashboard personnel** : Suivi de ses inscriptions et billets
- **Feedback** : Système d'évaluation post-événement

#### 🤖 Assistant IA
- **Génération de descriptions** : Création automatique de textes engageants
- **Suggestions** : Recommandations basées sur les événements similaires
- **Optimisation** : Analyse et amélioration des contenus

## 🏗️ Architecture Technique

### Backend (Django)
- **Framework** : Django 5.2 avec Django REST Framework
- **Base de données** : MySQL sur Azure avec SSL
- **Authentification** : JWT tokens avec rotation
- **API** : RESTful avec documentation Swagger/OpenAPI
- **Architecture** : Apps modulaires (users, organisations, events, inscriptions, payments, notifications, assistant, feedback)
- **Stockage** : Azure Blob Storage pour les médias
- **Sécurité** : CORS, HTTPS, HSTS en production

### Frontend (React)
- **Framework** : React 19.2 avec Vite
- **Routing** : React Router DOM v7
- **UI** : TailwindCSS 4.2 avec composants Lucide React
- **HTTP Client** : Axios avec intercepteurs et retry
- **Internationalisation** : i18next pour le multilingue
- **Animations** : Framer Motion pour les transitions
- **Tests** : Vitest avec Testing Library
- **Paiement** : Stripe React SDK
- **QR Codes** : qrcode.react pour les billets

### 📁 Structure du Projet

```
event-saas-back/
├── apps/
│   ├── users/           # Gestion utilisateurs et authentification
│   ├── organisations/   # Gestion organisations et rôles
│   ├── events/          # Gestion événements et assistant IA
│   ├── inscriptions/    # Gestion inscriptions et billets
│   ├── payments/        # Traitement paiements Stripe
│   ├── notifications/   # Système notifications temps réel
│   ├── assistant/       # Assistant IA et génération contenu
│   └── feedback/        # Système feedback et évaluations
├── config/
│   ├── settings/
│   │   ├── base.py      # Configuration de base
│   │   └── dev.py       # Configuration développement
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # WSGI pour déploiement
├── manage.py            # Script de gestion Django
├── requirements.txt     # Dépendances Python
├── Dockerfile           # Configuration Docker
└── azure-pipelines.yml # CI/CD Azure

event-saas-front/
├── src/
│   ├── pages/           # Pages de l'application
│   │   ├── Home.jsx     # Page d'accueil avec catalogue
│   │   ├── Login.jsx    # Connexion utilisateur
│   │   ├── Signup.jsx   # Inscription utilisateur
│   │   ├── gestionnaire/ # Dashboard gestionnaire
│   │   ├── participant/  # Dashboard participant
│   │   └── proprietaire/ # Dashboard propriétaire
│   ├── components/      # Composants réutilisables
│   ├── services/        # Services API et utilitaires
│   ├── contexts/        # Contextes React (state management)
│   ├── i18n/           # Configuration internationalisation
│   └── utils/          # Fonctions utilitaires
├── package.json        # Dépendances Node.js
├── vite.config.js      # Configuration Vite
├── tailwind.config.js  # Configuration TailwindCSS
├── Dockerfile          # Configuration Docker
└── azure-pipelines.yml # CI/CD Azure
```

## 🚀 Prérequis

### Système
- **Python** : 3.11+
- **Node.js** : 18+
- **MySQL** : 8.0+
- **Git** : 2.0+

### Services Externes
- **Azure** : Base de données MySQL et Blob Storage
- **Stripe** : Traitement des paiements
- **Navigateur** : Chrome/Firefox/Edge modernes

### Outils de Développement
- **IDE** : VS Code, PyCharm, ou WebStorm
- **Terminal** : PowerShell (Windows) ou Bash (Linux/Mac)
- **Docker** : Optionnel pour déploiement

## 📦 Installation

### 1. Cloner le Projet

```bash
git clone <repository-url>
cd event-saas-platform
```

### 2. Backend (Django)

#### Configuration Environnement Virtuel
```bash
cd event-saas-back
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### Installation Dépendances
```bash
pip install -r requirements.txt
```

#### Configuration Base de Données
Créer un fichier `.env` dans `event-saas-back/` :

```env
# Base de données Azure MySQL
DB_NAME=event_saas
DB_USER=votre_user_mysql
DB_PASSWORD=votre_password_mysql
DB_HOST=votre_server_mysql.mysql.database.azure.com
DB_PORT=3306
MYSQL_ATTR_SSL_CA=DigiCertGlobalRootG2.crt.pem

# Django
SECRET_KEY=votre_secret_key_django_très_long_et_aléatoire
DJANGO_ENV=development
ALLOWED_HOSTS=127.0.0.1,localhost

# Stripe
STRIPE_PUBLIC_KEY=pk_test_votre_clé_publique_stripe
STRIPE_SECRET_KEY=sk_test_votre_clé_secrète_stripe

# Azure Storage
AZURE_ACCOUNT_NAME=votre_compte_azure
AZURE_ACCOUNT_KEY=votre_clé_azure
AZURE_CONTAINER=event-media

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### Migration Base de Données
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Création Superutilisateur
```bash
python manage.py createsuperuser
```

#### Fichiers Statiques
```bash
python manage.py collectstatic --noinput
```

### 3. Frontend (React)

#### Installation Dépendances
```bash
cd event-saas-front
npm install
```

#### Configuration Environnement
Créer un fichier `.env.development` dans `event-saas-front/` :

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_STRIPE_PUBLIC_KEY=pk_test_votre_clé_publique_stripe
```

## 🏃‍♂️ Exécution

### 1. Démarrer le Backend

```bash
cd event-saas-back
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
python manage.py runserver
```

Le backend sera accessible sur `http://127.0.0.1:8000`

### 2. Démarrer le Frontend

```bash
cd event-saas-front
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173`

### 3. Accès aux Services

- **Application** : http://localhost:5173
- **Admin Django** : http://127.0.0.1:8000/admin
- **API Documentation** : http://127.0.0.1:8000/api/docs/
- **Health Check** : http://127.0.0.1:8000/health/

## 📖 Guide d'Utilisation

### 1. Configuration Initiale

#### Création Organisation
1. Accéder à `http://127.0.0.1:8000/admin`
2. Se connecter avec le superutilisateur
3. Dans "Organisations", créer une nouvelle organisation
4. Dans "Utilisateurs", créer des utilisateurs avec rôles appropriés

#### Configuration Stripe
1. Créer un compte Stripe (mode test)
2. Obtenir les clés API publique et secrète
3. Configurer les webhooks dans Stripe Dashboard
4. Ajouter les clés dans le fichier `.env`

### 2. Utilisation Quotidienne

#### Propriétaire d'Organisation
1. **Se connecter** : Utiliser le dashboard propriétaire
2. **Créer événement** : Remplir le formulaire avec l'aide de l'IA
3. **Publier** : Changer le statut de "brouillon" à "publié"
4. **Suivre** : Consulter les inscriptions et statistiques

#### Gestionnaire d'Événements
1. **Gérer événements** : Modifier et publier les événements existants
2. **Staff** : Assigner du personnel aux événements
3. **Notifications** : Envoyer des communications aux participants
4. **Analytics** : Analyser les performances des événements

#### Participant
1. **Explorer** : Parcourir le catalogue d'événements
2. **S'inscrire** : Cliquer sur "S'inscrire" et payer avec Stripe
3. **Recevoir billet** : Obtenir un billet QR code par email
4. **Évaluer** : Donner du feedback post-événement

### 3. Fonctionnalités Avancées

#### Assistant IA
```javascript
// Exemple d'utilisation de l'assistant
const response = await api.post('/assistant/generate-description', {
  titre: "Conférence Tech 2024",
  lieu: "Paris",
  capacite: 500,
  prix: 99.99
});
```

#### Paiements Stripe
```javascript
// Exemple de paiement
const stripe = await loadStripe(STRIPE_PUBLIC_KEY);
const { error } = await stripe.confirmPayment({
  clientSecret,
  confirmationMethod: 'pay',
  returnUrl: `${window.location.origin}/payment-success`,
});
```

#### Notifications Temps Réel
```javascript
// WebSocket pour notifications
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Traiter la notification
};
```

## 🔧 Configuration

### Variables d'Environnement

#### Backend (.env)
```env
# Base de données
DB_NAME=event_saas
DB_USER=azure_user
DB_PASSWORD=secure_password
DB_HOST=azure_server.mysql.database.azure.com
DB_PORT=3306

# Django
SECRET_KEY=django-secure-key-very-long-random-string
DJANGO_ENV=development
ALLOWED_HOSTS=127.0.0.1,localhost,yourdomain.com

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx

# Azure Storage
AZURE_ACCOUNT_NAME=storage_account
AZURE_ACCOUNT_KEY=storage_key
AZURE_CONTAINER=event-media

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

#### Frontend (.env.development)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_STRIPE_PUBLIC_KEY=pk_test_xxx
VITE_WS_URL=ws://localhost:8000/ws
```

### Configuration Production

#### HTTPS et Sécurité
```python
# settings/base.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

#### Base de Données Production
```python
# Utiliser Azure MySQL avec SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'ssl': {'ca': os.getenv('MYSQL_ATTR_SSL_CA')},
            'charset': 'utf8mb4',
        },
    }
}
```

## 🐛 Dépannage

### Problèmes Courants

#### Backend ne démarre pas
```bash
# Vérifier les dépendances
pip install -r requirements.txt

# Vérifier la base de données
python manage.py check

# Vérifier les migrations
python manage.py showmigrations

# Vérifier la configuration
python manage.py diffsettings
```

#### Erreur de connexion base de données
- Vérifier que MySQL Azure est accessible
- Confirmer les identifiants dans `.env`
- S'assurer que le certificat SSL est présent
- Tester avec un client MySQL externe

#### Erreur Stripe
- Vérifier les clés API (test vs production)
- Confirmer la configuration des webhooks
- Vérifier les domaines autorisés dans Stripe
- Tester avec les cartes de test Stripe

#### Frontend ne se connecte pas
- Vérifier que le backend est démarré
- Confirmer l'URL dans `VITE_API_BASE_URL`
- Vérifier la configuration CORS
- Consulter les logs du navigateur (F12)

#### Erreur 500 lors de l'inscription
```bash
# Logs détaillés du backend
python manage.py runserver --verbosity=2

# Vérifier les logs Azure
az webapp log tail --name <app-name> --resource-group <resource-group>

# Debug dans le code
import logging
logger = logging.getLogger(__name__)
logger.error("Erreur détaillée ici")
```

### Tests et Debug

#### Backend Tests
```bash
# Exécuter tous les tests
python manage.py test

# Tests spécifiques
python manage.py test apps.events.tests

# Coverage
coverage run --source='.' manage.py test
coverage report
```

#### Frontend Tests
```bash
# Exécuter les tests
npm test

# Tests avec coverage
npm run test:coverage

# Tests UI
npm run test:ui
```

#### API Testing
```bash
# Documentation API
curl http://127.0.0.1:8000/api/docs/

# Test endpoint
curl -H "Authorization: Bearer <token>" \
     http://127.0.0.1:8000/api/events/
```

## 🚀 Déploiement

### Azure App Service

#### Backend
```bash
# Build Docker image
docker build -t event-saas-back .

# Deploy to Azure
az webapp up --name event-saas-back --sku B1 --location westeurope
```

#### Frontend
```bash
# Build for production
npm run build

# Deploy to Azure Static Web App
az staticwebapp create \
  --name event-saas-front \
  --resource-group event-saas-rg \
  --source . \
  --location westeurope \
  --sku Standard
```

### Configuration Production

#### Variables d'Environnement Azure
```bash
# Set environment variables
az webapp config appsettings set \
  --name event-saas-back \
  --resource-group event-saas-rg \
  --settings DB_NAME=prod_db DB_USER=prod_user
```

#### SSL et Domaines
```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name event-saas-back \
  --resource-group event-saas-rg \
  --hostname yourdomain.com

# Add SSL certificate
az webapp config ssl bind \
  --webapp-name event-saas-back \
  --resource-group event-saas-rg \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNIEnabled
```

## 📊 Monitoring et Analytics

### Azure Monitor
```bash
# Enable Application Insights
az monitor app-insights component create \
  --app event-saas-insights \
  --location westeurope \
  --application-type web

# Connect to web app
az webapp config appsettings set \
  --name event-saas-back \
  --resource-group event-saas-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=<key>
```

### Logs et Métriques
```python
# Dans views.py
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def create_event(request):
    logger.info(f"Création événement par {request.user.email}")
    # ... code
    
    logger.info(f"Événement {event.id} créé avec succès")
```

## 🤝 Contribution

### Processus de Développement
1. Forker le repository
2. Créer une branche feature : `git checkout -b feature/nouvelle-fonctionnalité`
3. Faire les modifications
4. Tester : `npm test` et `python manage.py test`
5. Commit : `git commit -m "Add: nouvelle fonctionnalité"`
6. Push : `git push origin feature/nouvelle-fonctionnalité`
7. Pull Request

### Conventions de Code
- **Python** : PEP 8, noms de variables en français
- **JavaScript/JSX** : ESLint configuration, composants fonctionnels
- **Git** : Messages de commit conventionnels
- **API** : RESTful, documentation OpenAPI

### Code Review
- Revue obligatoire pour toute PR
- Tests requis pour nouvelles fonctionnalités
- Documentation mise à jour
- Performance et sécurité vérifiées

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

### Documentation
- **API Docs** : http://127.0.0.1:8000/api/docs/
- **Admin Guide** : http://127.0.0.1:8000/admin/
- **Code Comments** : Documentation inline dans le code

### Communauté
- **Issues GitHub** : Signaler des bugs et demander des fonctionnalités
- **Discussions** : Questions et suggestions d'amélioration
- **Wiki** : Guides et tutoriels détaillés

### Contact
- **Email** : support@event-saas.com
- **Slack** : #event-saas-community
- **Twitter** : @EventSaaSPlatform

---

**🎊 Développé avec passion pour simplifier la gestion d'événements modernes**

*Technologies : Django, React, Stripe, Azure, TailwindCSS, i18next*
