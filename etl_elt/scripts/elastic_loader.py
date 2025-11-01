import os
import requests
from requests.auth import HTTPBasicAuth

def create_index(index_name="reviews"):
    es_url = os.environ.get("ELASTIC_URL")
    es_user = os.environ.get("ELASTIC_USERNAME")
    es_pass = os.environ.get("ELASTIC_PASSWORD")
    ca_cert_path = os.environ.get("CA_CERT_PATH")

    if not all([es_url, es_user, es_pass, ca_cert_path]):
        raise EnvironmentError("Variables d'environnement manquantes.")

    auth = HTTPBasicAuth(es_user, es_pass)

    print("=== Création d’un index Elasticsearch ===")
    print(f"URL : {es_url}")
    print(f"Index : {index_name}")

    # Étape 1 : Vérifier la connexion
    r = requests.get(es_url, auth=auth, verify=ca_cert_path, timeout=15)
    r.raise_for_status()
    print("Connexion OK.")

    # Étape 2 : Supprimer l'index s'il existe (même s'il est corrompu)
    print(f"Vérification de l'existence de l'index '{index_name}'...")
    try:
        head_r = requests.head(f"{es_url}/{index_name}", auth=auth, verify=ca_cert_path, timeout=10)
        if head_r.status_code == 200:
            print(f"L’index '{index_name}' existe — suppression en cours...")
            del_r = requests.delete(f"{es_url}/{index_name}", auth=auth, verify=ca_cert_path, timeout=20)
            print(f"Réponse suppression : {del_r.status_code}")
        else:
            print(f"Aucun index '{index_name}' trouvé, création possible.")
    except Exception as e:
        print(f"Erreur pendant la suppression éventuelle : {e}")

    # Étape 3 : Créer un index neuf
    print("\nCréation du nouvel index...")
    settings = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        },
        "mappings": {
            "properties": {
                "review": {"type": "text"},
                "rating": {"type": "float"},
                "date": {"type": "date", "format": "yyyy-MM-dd||strict_date_optional_time"},
                "source": {"type": "keyword"}
            }
        }
    }

    resp = requests.put(
        f"{es_url}/{index_name}",
        auth=auth,
        json=settings,
        verify=ca_cert_path,
        timeout=30
    )
    print(f"Réponse création : {resp.status_code}")
    print(resp.text)

    # Étape 4 : Vérifier le statut final de l’index
    print("\nVérification du statut du cluster :")
    health = requests.get(
        f"{es_url}/_cluster/health/{index_name}?pretty",
        auth=auth,
        verify=ca_cert_path
    )
    print(health.text)
    print("Fin du processus.")

