"""
Module ETL (Extract, Transform, Load)

Ce fichier servira de point d'entrée pour orchestrer le pipeline ETL.
Les fonctions d'extraction, de transformation et de chargement seront
appelées ici lorsque le code sera prêt.
"""

import time
from extract.scrape_compagnies import *

def main_etl():
    """Fonction principale du pipeline ETL."""
    # TODO: Appelez les fonctions ici (extraction, transformation, chargement)
    company_list = ["www.showroomprive.com", "loaded.com", "westernunion.com", "justfly.com", "www.facebook.com"]

    # collect company information in a dataframe
    companies_df = create_company_data_dataframe(company_list)

    # write the content of companies_df to a csv file
    companies_df.to_csv("companies_information.csv")

    print(companies_df.head())
    # Petit délai pour éviter la fermeture immédiate du conteneur Docker
    time.sleep(5)


if __name__ == "__main__":
    print("Démarrage du script ETL...")
    main_etl()
