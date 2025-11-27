import os
import json
import re
import glob
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from airflow.decorators import task
from airflow.models import Variable

# ================================================================
# ============= TÂCHE 1 : Connexion Elasticsearch ================
# ================================================================
@task
def get_es_connection():
    """
    Initialise la connexion Elasticsearch et retourne 
    (es_url, auth, ca_cert_path).
    """
    es_url = Variable.get("ELASTIC_URL", default_var=None)
    es_user = Variable.get("ELASTIC_USERNAME", default_var=None)
    es_pass = Variable.get("ELASTIC_PASSWORD", default_var=None)
    ca_cert_path = Variable.get("CA_CERT_PATH", default_var=None)

    if not all([es_url, es_user, es_pass, ca_cert_path]):
        raise EnvironmentError("Variables d'environnement Elasticsearch manquantes.")

    auth = HTTPBasicAuth(es_user, es_pass)

    return {
        "url": es_url,
        "auth": (es_user, es_pass),
        "ca_cert": ca_cert_path
    }


# ================================================================
# ============= TÂCHE 2 : Recréation d’un index ==================
# ================================================================
@task
def create_index(es_info, index_name="reviews"):

    es_url = es_info["url"]
    es_user, es_pass = es_info["auth"]
    ca_cert = es_info["ca_cert"]
    auth = HTTPBasicAuth(es_user, es_pass)

    print(f"=== Vérification de l’index Elasticsearch : {index_name} ===")

    head_r = requests.head(f"{es_url}/{index_name}", auth=auth, verify=ca_cert)

    if head_r.status_code == 200:
        print(f"L’index '{index_name}' existe déjà. Passage au chargement des documents.")
        return index_name
    else:
        print(f"L’index '{index_name}' n’existe pas, création en cours...")

    settings = {
        "settings": {
            "index": {"number_of_shards": 1, "number_of_replicas": 0}
        },
        "mappings": {
            "properties": {
                "company_name": {"type": "keyword"},
                "user_name": {"type": "keyword"},
                "review_count": {"type": "integer"},
                "headline": {"type": "text"},
                "review": {"type": "text"},
                "review_date_absolute": {"type": "date", "format": "yyyy-MM-dd"},
                "response_date": {"type": "date", "format": "yyyy-MM-dd"},
                "rating": {"type": "float"},
                "source": {"type": "keyword"},
                "scraping_date": {"type": "date", "format": "yyyy-MM-dd"},
                "filename": {"type": "keyword"}
            }
        }
    }

    resp = requests.put(
        f"{es_url}/{index_name}",
        auth=auth,
        json=settings,
        verify=ca_cert
    )

    print(f"Réponse création : {resp.status_code}")
    print(resp.text)

    return index_name


# ================================================================
# ============= TÂCHE 3 : Import incrémental =====================
# ================================================================
@task
def load_reviews(es_info, index_name):

    es_url = es_info["url"]
    es_user, es_pass = es_info["auth"]
    ca_cert = es_info["ca_cert"]
    auth = HTTPBasicAuth(es_user, es_pass)

    base_path = "/opt/airflow/external_data"

    # =============================================
    # 1 - Lire la dernière date déjà importée
    # =============================================
    query = {
        "size": 1,
        "sort": [{"scraping_date": {"order": "desc"}}],
        "_source": ["scraping_date"]
    }

    resp = requests.post(
        f"{es_url}/{index_name}/_search",
        json=query,
        auth=auth,
        verify=ca_cert
    )

    hits = resp.json().get("hits", {}).get("hits", [])
    last_loaded_date = None

    if hits:
        last_loaded_date = hits[0]["_source"]["scraping_date"]
        last_loaded_date = datetime.strptime(last_loaded_date, "%Y-%m-%d")
        print(f"Dernière date importée : {last_loaded_date}")
    else:
        print("Aucun document importé pour l'instant")

    # =============================================
    # 2 - Parcourir tous les fichiers JSON du dossier
    # =============================================
    json_files = glob.glob(f"{base_path}/*.json")

    if not json_files:
        print("Aucun fichier JSON trouvé.")
        return True

    for json_path in json_files:

        filename = os.path.basename(json_path)

        # Extraction date (format : 20240215.json)
        match = re.match(r"(\d{8})", filename)
        if not match:
            print(f"Ignoré, pas de date dans le nom : {filename}")
            continue

        file_date = datetime.strptime(match.group(1), "%Y%m%d")

        # =============================================
        # 3 - Skip si déjà importé
        # =============================================
        if last_loaded_date and file_date <= last_loaded_date:
            print(f"Déjà importé : {filename}")
            continue

        print(f"Nouveau fichier à charger : {filename}")

        # =============================================
        # 4 - Lire le fichier
        # =============================================
        with open(json_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)

        # =============================================
        # 5 - Charger en bulk
        # =============================================
        bulk_lines = []

        for r in reviews:
            doc = {
                "company_name": r.get("company_name", ""),
                "user_name": r.get("user_name", "").strip(),
                "review_count": _extract_value(r.get("review_count")),
                "headline": r.get("headline", "").strip(),
                "review": r.get("comment_text", "").strip(),
                "review_date_absolute": _normalize_date(r.get("review_date_absolute")),
                "response_date": _normalize_date(r.get("response_date")),
                "rating": _extract_value(r.get("stars")),
                "source": "trustpilot",
                "scraping_date": file_date.strftime("%Y-%m-%d"),
                "filename": filename
            }

            bulk_lines.append(json.dumps({"index": {"_index": index_name}}))
            bulk_lines.append(json.dumps(doc))

        bulk_payload = "\n".join(bulk_lines) + "\n"

        resp = requests.post(
            f"{es_url}/_bulk",
            auth=auth,
            data=bulk_payload.encode("utf-8"),
            headers={"Content-Type": "application/x-ndjson"},
            verify=ca_cert
        )

        print(f"ES response : {resp.status_code}")
        print(resp.text[:300])

    return True


# ================================================================
# ============= HELPERS : non décorés ============================
# ================================================================
def _extract_value(value):
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else 0


def _normalize_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return None
