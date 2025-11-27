from elasticsearch import Elasticsearch
import os

def get_es_client():
    return Elasticsearch(
        hosts=[os.getenv("ELASTIC_URL")],
        basic_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),
        verify_certs=True,
        ca_certs=os.getenv("CA_CERT_PATH")
    )

def fetch_comments(company_name: str, size: int = 20):
    es = get_es_client()

    query = {
        "query": {
            "term": {
                "company_name": company_name.lower()
            }
        },
        "sort": [{"review_date_absolute": "desc"}],
        "_source": ["headline", "review", "rating", "review_date_absolute"]
    }

    resp = es.search(index="reviews", body=query, size=size)
    return [hit["_source"] for hit in resp["hits"]["hits"]]