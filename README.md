# Event SaaS Platform

Une plateforme SaaS complète pour la gestion d'événements 
## 📋 Présentation du Projet

Event SaaS est une application web moderne permettant aux organisations de créer, gérer et publier des événements. Les participants peuvent s'inscrire simplement aux événements publiés sans processus complexe de billetterie.
### 🎯 Fonctionnalités Principales

#### Pour les Organisateurs
- **Création d'événements** : Titre, description, lieu, dates, capacité, prix
- **Gestion des organisations** : Structure hiérarchique avec propriétaires et gestionnaires
- **Dashboard de gestion** : Interface intuitive pour gérer tous les aspects
- **Publication d'événements** : Statut brouillon → publié
- **Suivi des inscriptions** : Liste des participants par événement

#### Pour les Participants
- **Exploration d'événements** : Consultation des événements publiés
- **Inscription simple** : Un clic pour s'inscrire (sans billets)
- **Vérification des places** : Contrôle automatique de la disponibilité
- **Dashboard personnel** : Suivi de ses inscriptions

#### Pour les Administrateurs
- **Gestion des utilisateurs** : Création de comptes propriétaires, gestionnaires, participants
- **Gestion des organisations** : Administration des structures
- **Monitoring** : Vue d'ensemble de toutes les activités

## 🏗️ Architecture Technique

### Backend (Django)
- **Framework** : Django 5.2 avec Django REST Framework
- **Base de données** : MySQL avec SSL
- **Authentification** : JWT tokens
- **API** : RESTful avec documentation Swagger/OpenAPI
- **Architecture** : Apps modulaires (users, organisations, events, proprietaire)

### Frontend (React)
- **Framework** : React 19.2 avec Vite
- **Routing** : React Router DOM
- **UI** : TailwindCSS avec composants Lucide React
- **HTTP Client** : Axios avec intercepteurs pour authentification
- **Notifications** : React Toastify

### 📁 Structure du Projet

```
event-saas-back/
├── apps/
│   ├── users/           # Gestion des utilisateurs et authentification
│   ├── organisations/   # Gestion des organisations
│   ├── events/          # Gestion des événements et inscriptions
│   └── proprietaire/    # Interface propriétaires
├── config/
│   ├── settings/
│   │   ├── base.py      # Configuration de base
│   │   └── dev.py       # Configuration développement
│   └── urls.py          # URLs principales
├── manage.py            # Script de gestion Django
└── requirements.txt     # Dépendances Python

event-saas-front/
├── src/
│   ├── pages/           # Pages de l'application
│   │   ├── Home.jsx     # Page d'accueil
│   │   ├── Login.jsx    # Connexion
│   │   ├── Signup.jsx   # Inscription
│   │   └── gestionnaire/ # Dashboard gestionnaire
│   │   └── participant/  # Dashboard participant
│   ├── services/
│   │   └── api.js       # Configuration API
│   └── main.jsx         # Point d'entrée
├── package.json         # Dépendances Node.js
└── vite.config.js       # Configuration Vite
```

## 🚀 Prérequis

### Système
- Python 3.11+
- Node.js 18+
- MySQL 8.0+

### Outils
- Git
- Terminal/PowerShell
- Navigateur web moderne

## 📦 Étapes d'Installation

### 1. Cloner le Projet

```bash
git clone <repository-url>
cd event-saas-platform
```

### 2. Backend (Django)

#### Configuration de l'environnement virtuel
```bash
cd event-saas-back
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

#### Installation des dépendances
```bash
pip install -r requirements.txt
```

#### Configuration de la base de données
1. Créer une base de données MySQL nommée `event_saas`
2. Configurer les variables d'environnement dans `.env` :

```env
DB_NAME=event_saas
DB_USER=votre_user_mysql
DB_PASSWORD=votre_password_mysql
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=votre_secret_key_django
```

#### Migration de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Création du superutilisateur
```bash
python manage.py createsuperuser
```

### 3. Frontend (React)

#### Installation des dépendances
```bash
cd event-saas-front
npm install
```

#### Configuration de l'environnement
Créer un fichier `.env` dans `event-saas-front/` :

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 🏃‍♂️ Étapes d'Exécution

### 1. Démarrer le Backend

```bash
cd event-saas-back
python manage.py runserver
```

Le backend sera accessible sur `http://127.0.0.1:8000`

### 2. Démarrer le Frontend

```bash
cd event-saas-front
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173`

## 📖 Guide d'Utilisation

### 1. Première Configuration

#### Création des organisations
1. Accéder à `http://127.0.0.1:8000/admin`
2. Se connecter avec le superutilisateur
3. Créer une organisation dans la section "Organisations"
4. Créer des utilisateurs propriétaires et gestionnaires

#### Création des utilisateurs
1. **Propriétaires** : Peuvent créer des événements pour leur organisation
2. **Gestionnaires** : Peuvent gérer les événements existants
3. **Participants** : Peuvent s'inscrire aux événements

### 2. Utilisation Quotidienne

#### Pour les Organisateurs
1. **Se connecter** : Utiliser le dashboard gestionnaire
2. **Créer un événement** : Remplir le formulaire avec les détails
3. **Publier l'événement** : Changer le statut de "brouillon" à "publié"
4. **Suivre les inscriptions** : Consulter la liste des participants

#### Pour les Participants
1. **Explorer** : Visiter la page d'accueil pour voir les événements
2. **S'inscrire** : Cliquer sur "S'inscrire" sur un événement disponible
3. **Confirmation** : Recevoir la confirmation immédiate
4. **Suivi** : Consulter ses inscriptions dans son dashboard

### 3. Fonctionnalités Avancées

#### API REST
L'API est accessible via `http://127.0.0.1:8000/api/` avec documentation :
- Swagger UI : `http://127.0.0.1:8000/api/docs/`
- OpenAPI Schema : `http://127.0.0.1:8000/api/schema/`

#### Endpoints Principaux
- `GET /api/events/public-events/` : Lister les événements publics
- `POST /api/events/simple-register/` : Inscription simple
- `GET /api/events/evenements/` : Gestion des événements (authentifié)
- `POST /api/users/login/` : Connexion
- `POST /api/users/register/` : Inscription utilisateur

## 🔧 Configuration

### Variables d'Environnement

#### Backend (.env)
```env
# Base de données
DB_NAME=event_saas
DB_USER=votre_user
DB_PASSWORD=votre_password
DB_HOST=localhost
DB_PORT=3306

# Django
SECRET_KEY=votre_secret_key_ici
DEBUG=True

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_password
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### Personnalisation

#### Modification des styles
- Les styles sont gérés avec TailwindCSS
- Fichier de configuration : `tailwind.config.js`
- Classes personnalisées dans les composants React

#### Extension des fonctionnalités
- Ajouter de nouveaux modèles dans `apps/*/models.py`
- Créer de nouvelles vues dans `apps/*/views.py`
- Ajouter des routes dans `apps/*/urls.py`

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
```

#### Erreur de connexion à la base de données
- Vérifier que MySQL est en cours d'exécution
- Confirmer les identifiants dans `.env`
- S'assurer que la base de données existe

#### Frontend ne se connecte pas au backend
- Vérifier que le backend est bien démarré
- Confirmer l'URL dans `VITE_API_BASE_URL`
- Vérifier les CORS dans les settings Django

#### Erreur 500 lors de l'inscription
- Vérifier les logs du backend : `python manage.py runserver --verbosity=2`
- Confirmer que les migrations sont appliquées
- Vérifier les permissions de l'utilisateur

### Logs et Debug

#### Backend
```bash
# Logs détaillés
python manage.py runserver --verbosity=2

# Vérifier les modèles
python manage.py shell
>>> from apps.events.models import Evenement
>>> Evenement.objects.all()
```

#### Frontend
- Ouvrir les outils de développement du navigateur
- Consulter l'onglet "Console" pour les erreurs
- Vérifier l'onglet "Network" pour les requêtes API

## 📝 Notes de Développement

### Conventions de Code
- **Backend** : PEP 8, noms de variables en français
- **Frontend** : JSX, composants fonctionnels avec hooks
- **API** : RESTful, réponses JSON structurées

### Sécurité
- JWT tokens pour l'authentification
- CORS configuré pour le frontend
- Validation des entrées côté serveur
- HTTPS recommandé en production

### Performance
- Pagination pour les listes d'événements
- Mise en cache des données statiques
- Optimisation des images avec Vite

## 🤝 Contribution

Pour contribuer au projet :
1. Forker le repository
2. Créer une branche feature
3. Faire les modifications
4. Tester avec `python manage.py test` et `npm test`
5. Soumettre une pull request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Consulter la documentation API
- Vérifier les logs pour le debug

---

**Développé avec ❤️ pour simplifier la gestion d'événements**
