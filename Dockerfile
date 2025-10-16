# Image de Base
FROM python:3.11-slim

# Dossier de travail
WORKDIR /app

# Copier les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code du projet
COPY . .

# Création de dossier
#RUN mkdir -p data/raw # Création du dossier en local ou via le programe

# Exécuter en tant que utilisateur non-root
RUN useradd -m appuser
USER appuser

# Commande par défaut pour exécuter le pipeline
CMD [ "python", "etl.py" ]