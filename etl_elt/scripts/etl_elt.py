"""
Module ETL (Extract, Transform, Load)

Ce fichier servira de point d'entrée pour orchestrer le pipeline ETL.
Les fonctions d'extraction, de transformation et de chargement seront
appelées ici lorsque le code sera prêt.
"""

import time
from scrape_company_metadatas import *

def main_etl():

    outputFolder = "/app/extracts/"
    """Fonction principale du pipeline ETL."""
    # TODO: Appelez les fonctions ici (extraction, transformation, chargement)
    company_list = ["www.showroomprive.com", "loaded.com", "westernunion.com", "justfly.com", "www.facebook.com"]
    # collect company metadatas in a dataframe
    companies_df = create_company_data_dataframe(company_list)

    # write the content of companies_df to a csv file
    #companies_df.to_csv("./extract/data/companies_information.csv")
    #companies_df.to_csv("/app/extracts/companies_information.csv")
    companies_df.to_csv(outputFolder + "companies_metadatas.csv")

    # Petit délai pour éviter la fermeture immédiate du conteneur Docker
    time.sleep(5)


if __name__ == "__main__":
    print("Démarrage du script ETL...")
    main_etl()