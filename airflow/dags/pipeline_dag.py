from airflow.decorators import dag
from datetime import datetime

# --- Import scraping reviews ---
from tasks.scrape_reviews import (
    get_scrape_window,
    scrape_reviews,
    update_scrape_window,
)

# --- Import Elasticsearch loader ---
from tasks.elastic_loader import (
    get_es_connection,
    create_index,
    load_reviews,
)

# --- Import metadata scraping ---
from tasks.scrape_metadatas import extract_company_metadata

# --- Import metadata PostgreSQL loader ---
from tasks.postgres_loader import (
    create_metadata_tables,
    load_company_metadata_to_postgres
)

# Liste d'entreprises pour les métadonnées
COMPANIES = [
    "www.showroomprive.com",
    "www.amazon.fr",
    "www.apple.com",
    "www.aliexpress.com",
    "www.justfly.com",
    "www.westernunion.com",
    "www.loaded.com",
]

# Chemin de sortie du fichier metadata
META_DATA_PATH = "/opt/airflow/meta_data/companies_metadata.csv"


@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["elasticsearch", "scraping", "metadata"]
)
def pipeline_reviews():

    # Scraping des métadonnées Trustpilot
    company_metadata_file = extract_company_metadata(
        companies=COMPANIES,
        output_path=META_DATA_PATH
    )

    # Création des tables PostgreSQL (idempotent)
    tables_created = create_metadata_tables()

    # Chargement des métadonnées (skip automatique si CSV identique)
    metadata_loaded = load_company_metadata_to_postgres(company_metadata_file)

    # Chaînage metadata
    company_metadata_file >> tables_created >> metadata_loaded

    # Lecture de la fenêtre de scraping reviews
    window = get_scrape_window()
    metadata_loaded >> window

    # Scraping des reviews Trustpilot
    scraped_file = scrape_reviews(window)

    # Mise à jour de la fenêtre pour le prochain run
    next_window = update_scrape_window(window)

    # Connexion à Elasticsearch
    es_info = get_es_connection()

    # Création de l'index si non existant
    index_name = create_index(es_info, index_name="reviews")

    # Chargement incrémental des reviews
    load_reviews(es_info, index_name) << scraped_file


pipeline_reviews()
