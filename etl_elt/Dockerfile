# Image de Base
FROM python:3.11-slim

# Dossier de travail
WORKDIR /app

# Copier les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code du projet
# Pour le moment, on ne fait pas, on crée un volume dans le docker compose qui pointe vers le répertoire contenant les scripts
# COPY ./scripts /app/scripts

# Exécuter en tant que utilisateur non-root

RUN useradd -m appuser
USER appuser

# Commande pour exécuter le pipeline
# On ne fait pas ici, la commande est appelée dans le docker-compose
# RUN python /app/scripts/etl_elt.py