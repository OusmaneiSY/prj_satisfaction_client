"""
Module ETL (Extract, Transform, Load)

Ce fichier servira de point d'entrée pour orchestrer le pipeline ETL.
Les fonctions d'extraction, de transformation et de chargement seront
appelées ici lorsque le code sera prêt.
"""

import time


def main_etl():
    """Fonction principale du pipeline ETL."""
    # TODO: Appelez les fonctions ici (extraction, transformation, chargement)

    # Petit délai pour éviter la fermeture immédiate du conteneur Docker
    time.sleep(5)


if __name__ == "__main__":
    print("Démarrage du script ETL...")
    main_etl()