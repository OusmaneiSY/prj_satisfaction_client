FROM python:3.10-slim

WORKDIR /app

# Optimisation
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean

# Installation dépendances Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Télécharger modèle SpaCy FR
RUN python -m spacy download fr_core_news_md

# Copier le code
COPY scripts/ /app/

# Exposer port FastAPI
EXPOSE 8000

# Lancement serveur FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
