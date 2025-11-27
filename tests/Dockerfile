FROM python:3.10-slim

WORKDIR /app

# Optimisations Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean

# Install test dependencies
COPY tests/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Installation modèle Spacy fr_core_news_md (OBLIGATOIRE pour le test)
RUN python -m spacy download fr_core_news_md


# Copy API SCRIPTS ONLY
COPY api/scripts /app/

# Copy ML scripts only
COPY ml/scripts /app/ml/scripts

#Copy modèle ML
COPY ml/models/ /app/models/

# Copy test scripts
COPY tests/scripts /app/tests/scripts

# Run tests
CMD ["pytest", "-vv", "/app/tests/scripts"]

# Faire attention quand la structure du dockerfile n'est pas flat
# Autre alternative pour éviter ENV PYTHONPATH="/app:${PYTHONPATH}"
# CMD ["sh", "-c", "cd /app && pytest -vv tests/scripts"]
