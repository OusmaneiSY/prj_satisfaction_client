from airflow.decorators import dag
from datetime import datetime

from tasks.scrape_reviews import (
    get_scrape_window,
    scrape_reviews,
    update_scrape_window,
)

from tasks.elastic_loader import (
    get_es_connection,
    create_index,
    load_reviews,
)

@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["elasticsearch", "scraping"]
)
def pipeline_reviews():


    # 0. Lire la fenêtre de scraping actuelle (last12months, last6months, ...)
    window = get_scrape_window()

    # 1. Scraper toutes les entreprises pour cette fenêtre
    scraped_file = scrape_reviews(window)

    # 2. Mettre à jour la fenêtre pour le prochain run
    next_window = update_scrape_window(window)

    # 3. Connexion à Elasticsearch
    es_info = get_es_connection()

    # 4. Création de l'index si non existant
    index_name = create_index(es_info, index_name="reviews")

    # 5. Chargement incrémental de TOUS les fichiers du dossier
    load_reviews(es_info, index_name) << scraped_file

pipeline_reviews()
