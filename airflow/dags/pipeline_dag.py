from airflow.decorators import dag
from datetime import datetime

from tasks.elastic_loader import (
    get_es_connection,
    create_index,
    load_reviews
)

@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["elasticsearch", "scraping"]
)
def pipeline_reviews():

    # 1. Connexion à Elasticsearch
    es_info = get_es_connection()

    # 2. Création de l'index si non existant
    index_name = create_index(es_info, index_name="reviews")

    # 3. Chargement incrémental de TOUS les fichiers du dossier
    load_reviews(es_info, index_name)

pipeline_reviews()
