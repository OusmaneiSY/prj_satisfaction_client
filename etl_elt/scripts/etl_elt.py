"""
Module ETL (Extract, Transform, Load)

Ce fichier servira de point d'entrée pour orchestrer le pipeline ETL.
Les fonctions d'extraction, de transformation et de chargement seront
appelées ici lorsque le code sera prêt.
"""

import time
from scrape_company_metadatas import *
from elastic_loader import create_index


def main_etl_elt():

    # répertoire de sortie
    #outputFolder = "/app/extracts/"

    """Fonction principale du pipeline ETL."""
    # TODO: Appelez les fonctions ici (extraction, transformation, chargement)
    #company_list = ["www.showroomprive.com", "loaded.com", "westernunion.com", "justfly.com", "www.facebook.com"]

    # collect company metadatas in a dataframe
    #companies_metadatas_df = create_company_data_dataframe(company_list)

    # write the content of companies_df to a csv file
    #companies_metadatas_df.to_csv(outputFolder + "companies_metadatas.csv")

    # Petit délai pour éviter la fermeture immédiate du conteneur Docker
    #time.sleep(5)
    print("Création de l’index Elasticsearch")
    try:
        create_index('reviews')
        print("Création d’index terminée avec succès.")
    except Exception as e:
        print(f"Erreur durant l’étape Elasticsearch : {e}")

    print("Fin du processus ETL.")

if __name__ == "__main__":
    print("Démarrage du script ETL...")
    main_etl_elt()