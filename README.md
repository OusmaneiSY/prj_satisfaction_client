[![CI - Sentiment Analysis API](https://github.com/DataScientest-Studio/sep25_bde_satisfaction_b/actions/workflows/ci.yml/badge.svg?branch=osy_branch)](https://github.com/DataScientest-Studio/sep25_bde_satisfaction_b/actions/workflows/ci.yml)
# Projet : Satisfaction Client dans la Supply Chain

## Présentation et Objectifs
Ce projet, réalisé dans le cadre de la formation Data Engineer de DataScientest, vise à analyser la satisfaction client à partir d'avis collectés en ligne, principalement depuis Trustpilot. L'objectif est de mesurer, synthétiser et visualiser ces avis, tout en automatisant leur collecte, leur traitement et leur mise à jour.

L'analyse couvre plusieurs dimensions clés de la supply chain : conception des produits, logistique et délais de livraison, tarification, durabilité et adéquation globale aux attentes du marché.

## Étapes du Projet

### 1. Extraction des Données
- Extraction d'avis clients via scraping.
- Enregistrement en JSON et CSV.
- Outils : Python (Requests, BeautifulSoup, Pandas).

### 2. Organisation de la Donnée
- Stockage structuré dans PostgreSQL.
- Indexation documentaire dans Elasticsearch.
- Visualisation dans Kibana.

### 3. Analyse et Machine Learning
- Analyse de sentiment sur les textes collectés.
- Notebook détaillé et reproductible.
- Outils : Scikit-learn, Pandas, SpaCy, Wordcloud.

### 4. Mise en Production
- Déploiement des modèles via une API.
- Conteneurisation complète.
- Outils : FastAPI, Docker.

### 5. Automatisation et Monitoring
- Pipeline Airflow pour orchestrer les tâches.
- Monitoring complet avec Prometheus et Grafana.
- CI via GitHub Actions.

---

## Installation et Lancement via Docker
L'ensemble du projet fonctionne via Docker pour garantir une exécution reproductible sur Windows, Linux ou macOS.

### Prérequis
- Docker Desktop (Windows et macOS) ou Docker Engine (Linux)

Vérification :
```
docker --version
docker compose version
```

### Lancement du Projet
1. Cloner le dépôt :
```
git clone <lien_du_dépôt_github>
cd sep25_bde_satisfaction_b
```

2. Démarrer les services :
```
docker compose up -d
```

Les services suivants seront disponibles : Airflow, API FastAPI, Jupyter ML, Elasticsearch, Kibana, Prometheus, Grafana.

---

## Accès aux Services Principaux

### Airflow
- Interface Web : accessible via le port configuré (par défaut 8080 si exposé).
- Conteneurs actifs : scheduler, worker, triggerer, dag-processor, api-server.

### Jupyter Notebook (Machine Learning)
Accès via :
```
http://localhost:8888
```
ou, sur machine virtuelle :
```
http://<IP_VM>:8888
```

### API FastAPI (Analyse de sentiment)
Accessible via la documentation interactive :
- En local :
```
http://localhost:8000/docs
```
- Via machine virtuelle ou serveur :
```
http://<IP_VM>:8000/docs
```

### Elasticsearch et Kibana
- Elasticsearch sécurisé (HTTPS).
- Kibana :
```
http://<IP>:5601
```

### Monitoring (Prometheus et Grafana)
- Prometheus :
```
http://<IP>:9090
```
- Grafana :
```
http://<IP>:3000
```

---

## Structure du Projet
```
project_root/
│
├── airflow/
│   ├── dags/
│   ├── logs/
│   ├── plugins/
│   └── config/
│
├── api/
│   ├── scripts/
│   ├── models/
│   └── Dockerfile
│
├── ml/
│   ├── scripts/
│   ├── data/
│   ├── models/
│   ├── notebooks/
│   └── Dockerfile
│
├── monitoring/
│   └── prometheus.yml
│
├── certs/
├── docker-compose.yml
├── .env
└── README.md
```

---

## Ajout de Code

### Exemple dans le module ML
Fichier : `ml/scripts/my_cleaner.py`
```
def clean_data():
    print("Nettoyage des données")
```
Utilisation :
```
from ml.scripts.my_cleaner import clean_data
clean_data()
```

### Exemple dans l'API
Fichier : `api/scripts/predict.py`
```
def predict(text):
    return {"sentiment": "positive"}
```
Ce fichier est monté automatiquement dans le conteneur.

---

## Variables d'Environnement
Un fichier `.env` centralise les paramètres sensibles :
- Accès Elasticsearch (SSL, identifiants)
- Credentiels API
- Paramètres Airflow
- Configurations PostgreSQL

Ce fichier est chargé automatiquement par Docker Compose.

---

## Generation des certificats Elasticsearch
Les certificats utilises pour securiser Elasticsearch sont generes manuellement et stockes dans le dossier `certs/`.

### 1. Generer la CA (Certificate Authority)
```
docker run --rm \
  -v ./certs:/certs \
  docker.elastic.co/elasticsearch/elasticsearch:9.2.0 \
  elasticsearch-certutil ca --pem \
  --out /certs/ca.zip
```
Extraire la CA :
```
unzip certs/ca.zip -d certs
```
Structure obtenue :
```
certs/ca/
  ca.crt
  ca.key
```

### 2. Generer le certificat serveur Elasticsearch
```
docker run --rm \
  -v ./certs:/certs \
  docker.elastic.co/elasticsearch/elasticsearch:9.2.0 \
  elasticsearch-certutil cert --pem \
  --ca-cert /certs/ca/ca.crt \
  --ca-key /certs/ca/ca.key \
  --out /certs/es.zip \
  --name elasticsearch
```
Extraire les fichiers :
```
unzip certs/es.zip -d certs
```
Structure obtenue :
```
certs/elasticsearch/
  elasticsearch.crt
  elasticsearch.key
```
Ces chemins correspondent exactement aux parametres utilises dans le `docker-compose.yml`.

---

## Équipe du Projet

- Ousmane Ibrahima SY [LinkedIn](https://www.linkedin.com/in/ousmane-sy-6926a6139) / [GitHub](https://github.com/Oussouke)

