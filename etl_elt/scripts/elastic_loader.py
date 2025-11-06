import os
import json
import re
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth


# ================================================================
# === Connexion Elasticsearch (centralisée)
# ================================================================
def get_es_connection():
    """
    Initialise et retourne les objets nécessaires à la connexion Elasticsearch.
    """
    es_url = os.environ.get("ELASTIC_URL")
    es_user = os.environ.get("ELASTIC_USERNAME")
    es_pass = os.environ.get("ELASTIC_PASSWORD")
    ca_cert_path = os.environ.get("CA_CERT_PATH")

    if not all([es_url, es_user, es_pass, ca_cert_path]):
        raise EnvironmentError("Variables d'environnement Elasticsearch manquantes.")

    auth = HTTPBasicAuth(es_user, es_pass)
    return es_url, auth, ca_cert_path


# ================================================================
# === Création d’un index
# ================================================================
def create_index(es_url, auth, ca_cert_path, index_name="reviews"):
    """
    Supprime et recrée un index Elasticsearch avec le mapping adapté aux reviews.
    """
    print("=== Création d’un index Elasticsearch ===")
    print(f"URL : {es_url}")
    print(f"Index : {index_name}")

    # Étape 1 : Vérifier la connexion
    try:
        r = requests.get(es_url, auth=auth, verify=ca_cert_path, timeout=15)
        r.raise_for_status()
        print("Connexion OK.")
    except Exception as e:
        raise ConnectionError(f"Erreur de connexion à Elasticsearch : {e}")

    # Étape 2 : Supprimer l’index s’il existe
    print(f"Vérification de l'existence de l'index '{index_name}'...")
    head_r = requests.head(f"{es_url}/{index_name}", auth=auth, verify=ca_cert_path, timeout=10)
    if head_r.status_code == 200:
        print(f"L’index '{index_name}' existe — suppression en cours...")
        del_r = requests.delete(f"{es_url}/{index_name}", auth=auth, verify=ca_cert_path, timeout=20)
        print(f"Réponse suppression : {del_r.status_code}")
    else:
        print("Aucun index trouvé, création possible.")

    # Étape 3 : Créer le nouvel index
    settings = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
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
            }
        }
    }

    print("Création du nouvel index...")
    resp = requests.put(
        f"{es_url}/{index_name}",
        auth=auth,
        json=settings,
        verify=ca_cert_path,
        timeout=30
    )
    print(f"Réponse création : {resp.status_code}")
    print(resp.text)

    # Étape 4 : Vérifier la santé de l’index
    health = requests.get(
        f"{es_url}/_cluster/health/{index_name}?pretty",
        auth=auth,
        verify=ca_cert_path
    )
    print(health.text)
    print("Fin du processus de création.\n")


# ================================================================
# === Importation des reviews
# ================================================================
def load_reviews_to_elasticsearch(es_url, auth, ca_cert_path, index_name="reviews", companies=None):
    """
    Parcourt une liste d’entreprises, lit leurs fichiers JSON dans /app/extracts/,
    nettoie les données et les indexe en bulk dans Elasticsearch.
    """
    if companies is None:
        companies = []

    # Recréation d’un index propre avant import
    create_index(es_url, auth, ca_cert_path, index_name=index_name)

    for company in companies:
        json_path = f"/app/extracts/{company}.json"
        output_path = f"/app/extracts/{company}_clean.json"

        if not os.path.exists(json_path):
            print(f"Fichier introuvable pour {company} : {json_path}")
            continue

        print(f"=== Import des reviews pour {company} ===")

        # Lecture du JSON
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                reviews = json.load(f)
        except Exception as e:
            print(f"Erreur de lecture {json_path} : {e}")
            continue
        # Tester l'index sur du json
        """""
        cleaned_data = []
        for r in reviews:
            review_count = _extract_review_count(r.get("review_count", "0"))
            doc = {
                "company_name": company,
                "user_name": r.get("user_name", "").strip(),
                "review_count": review_count,
                "headline": r.get("headline", "").strip(),
                "review": r.get("comment_text", "").strip(),
                "review_date_absolute": _normalize_date(r.get("review_date_absolute")),
                "response_date": _normalize_date(r.get("response_date")),
                "rating": _extract_rating(r.get("user_score-src")),
                "source": "trustpilot"
            }
            cleaned_data.append(doc)

        # === Sauvegarde du JSON nettoyé ===
        os.makedirs("/app/extracts", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(cleaned_data, out, ensure_ascii=False, indent=2)

        print(f"Fichier nettoyé sauvegardé : {output_path} ({len(cleaned_data)} reviews)")

        """""
        bulk_data = []
        for r in reviews:
            review_count = _extract_value(r.get("review_count", "0"))
            rating = _extract_value(r.get("stars", "0"))
            doc = {
                "company_name": company,
                "user_name": r.get("user_name", "").strip(),
                "review_count": review_count,
                "headline": r.get("headline", "").strip(),
                "review": r.get("comment_text", "").strip(),
                "review_date_absolute": _normalize_date(r.get("review_date_absolute")),
                "response_date": _normalize_date(r.get("response_date")),
                "rating": rating,
                "source": "trustpilot"
            }

            bulk_data.append(json.dumps({"index": {"_index": index_name}}))
            bulk_data.append(json.dumps(doc))

        # Envoi en bulk
        if not bulk_data:
            print(f"Aucune donnée valide pour {company}")
            continue

        bulk_payload = "\n".join(bulk_data) + "\n"
        resp = requests.post(
            f"{es_url}/_bulk",
            auth=auth,
            data=bulk_payload.encode("utf-8"),
            headers={"Content-Type": "application/x-ndjson"},
            verify=ca_cert_path,
            timeout=90
        )

        if resp.status_code == 200 and '"errors":false' in resp.text:
            print(f"Import terminé pour {company} ({len(reviews)} reviews)")
        else:
            print(f"Erreur import {company} : {resp.status_code}")
            print(resp.text[:500])  # limiter la sortie"""


# ================================================================
# === Utils (extraction et nettoyage)
# ================================================================
def _extract_value(value):
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else 0


def _normalize_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
    except Exception:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            return None

