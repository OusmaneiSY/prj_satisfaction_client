import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs
from airflow.decorators import task
import os


def get_company_data_from_trustpilot(company_name):
    """
    Télécharge la page Trustpilot d'une entreprise.
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    url = f"https://www.trustpilot.com/review/{company_name}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.content


def parse_company_data(company_html):
    """
    Parse le HTML Trustpilot pour extraire les métadonnées de l’entreprise.
    """
    soup = bs(company_html, "lxml")
    raw = soup.find("script", attrs={"id": "__NEXT_DATA__"})
    data = json.loads(raw.text)

    business = data["props"]["pageProps"]["businessUnit"]

    # Catégorie principale
    if len(business["categories"]) == 1:
        category = business["categories"][0]["name"]
    else:
        category = next(
            c["name"] for c in business["categories"] if c.get("isPrimary")
        )

    return {
        "id": business["id"],
        "displayName": business["displayName"],
        "numberOfReviews": business["numberOfReviews"],
        "trustScore": business["trustScore"],
        "websiteUrl": business["websiteUrl"],
        "stars": business["stars"],
        "category": category,
        "email": business["contactInfo"]["email"],
        "address": business["contactInfo"]["address"],
        "city": business["contactInfo"]["city"],
        "country": business["contactInfo"]["country"],
        "phone": business["contactInfo"]["phone"],
        "zipCode": business["contactInfo"]["zipCode"],
        "five_star_percentage": soup.find("label", {"data-star-rating": "five"})
            .find_next("p", {
                "data-rating-distribution-row-percentage-typography": "true"
            }).text,
        "four_star_percentage": soup.find("label", {"data-star-rating": "four"})
            .find_next("p", {
                "data-rating-distribution-row-percentage-typography": "true"
            }).text,
        "three_star_percentage": soup.find("label", {"data-star-rating": "three"})
            .find_next("p", {
                "data-rating-distribution-row-percentage-typography": "true"
            }).text,
        "two_star_percentage": soup.find("label", {"data-star-rating": "two"})
            .find_next("p", {
                "data-rating-distribution-row-percentage-typography": "true"
            }).text,
        "one_star_percentage": soup.find("label", {"data-star-rating": "one"})
            .find_next("p", {
                "data-rating-distribution-row-percentage-typography": "true"
            }).text,
    }


@task
def extract_company_metadata(companies: list, output_path: str):
    """
    Scrape uniquement si le fichier metadata n'existe pas encore.
    Si le CSV existe déjà : skip automatique.
    """
    # Skip pour éviter de scraper plusieurs fois
    if os.path.exists(output_path):
        print(f"Le fichier {output_path} existe déjà - skip scraping.")
        return output_path

    rows = []

    for company in companies:
        html = get_company_data_from_trustpilot(company)
        parsed = parse_company_data(html)
        rows.append(parsed)

    df = pd.DataFrame(rows)
    df.set_index("id", inplace=True)
    df.to_csv(output_path)

    print(f"Fichier metadata généré : {output_path}")
    return output_path
