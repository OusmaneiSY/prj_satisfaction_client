import os
import json
import time
import random
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from airflow.decorators import task
from airflow.models import Variable

BASE_PATH = "/opt/airflow/external_data"
BASE_URL = "https://www.trustpilot.com/review"

# Toutes les entreprises à scraper
COMPANIES = [
    "www.showroomprive.com",
    "www.amazon.fr",
    "www.apple.com",
    "www.aliexpress.com",
    "www.justfly.com",
    "www.westernunion.com",
    "www.loaded.com",
]

# Ordre des fenêtres de temps
WINDOW_ORDER = [
    "last12months",
    "last6months",
    "last3months",
    "last30days",
    "all",
]

MAX_PAGES_PER_COMPANY = 5  # 5 premières pages car le scraping est interdit et bloqué par trustpilot, ceci n'est qu'u demo


def _clean(text: str) -> str:
    return text.strip().replace("\n", " ") if text else ""


def _build_url(company: str, window: str, page: int) -> str:
    """
    Construit l'URL Trustpilot en fonction de la fenêtre de temps et de la page.
    - window ∈ {"last12months", "last6months", "last3months", "last30days", "all"}
    Cette logique est mis en place pour faire un démo de scrapping car le scrapping est interdit par trustpilot
    """
    base = f"{BASE_URL}/{company}"
    params = []

    if window != "all":
        params.append(f"date={window}")

    # langue + avis vérifiés
    params.append("languages=fr")
    params.append("verified=true")
    params.append(f"page={page}")

    return base + "?" + "&".join(params)


@task
def get_scrape_window() -> str:
    """
    Lit la fenêtre de temps courante depuis une Variable Airflow.
    Si absente / invalide -> initialise à 'last12months'.
    """
    window = Variable.get("SCRAPE_WINDOW", default_var="last12months")
    if window not in WINDOW_ORDER:
        window = "last12months"
        Variable.set("SCRAPE_WINDOW", window)

    print(f"[get_scrape_window] Fenêtre de scraping courante : {window}")
    return window


@task
def scrape_reviews(window: str) -> str:
    """
    Scrape toutes les entreprises de COMPANIES pour la fenêtre 'window'
    (last12months, last6months, last3months, last30days, all)
    et écrit un seul fichier JSON dans BASE_PATH.

    Retourne le chemin du fichier généré.
    """

    headers = {"User-Agent": "Mozilla/5.0"}
    all_reviews = []

    print(f"[scrape_reviews] Démarrage scraping pour fenêtre : {window}")

    os.makedirs(BASE_PATH, exist_ok=True)

    for company in COMPANIES:
        company_short = (
            company.replace("www.", "")
            .replace(".com", "")
            .replace(".fr", "")
        )

        print(f"[scrape_reviews] --- Entreprise : {company} ---")

        review_counter = 1  

        for page in range(1, MAX_PAGES_PER_COMPANY + 1):
            url = _build_url(company, window, page)
            print(f"[scrape_reviews] URL : {url}")

            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 404:
                    print(f"[scrape_reviews] Page 404, arrêt pour {company} page {page}")
                    break
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[scrape_reviews] Erreur HTTP sur {url} : {e}")
                # On passe à la page suivante ou à la prochaine entreprise
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("article[data-service-review-card-paper='true']")
            print(f"[scrape_reviews] {len(cards)} reviews trouvées pour {company}, page {page}")

            if not cards:
                # Plus d'avis pour cette fenêtre / entreprise
                break

            for card in cards:
                user_tag = card.select_one("[data-consumer-name-typography='true']")
                user_name = _clean(user_tag.text) if user_tag else ""

                review_count_tag = card.select_one("[data-consumer-reviews-count]")
                val = (
                    review_count_tag.get("data-consumer-reviews-count")
                    if review_count_tag else None
                )
                review_count = f"{val} reviews" if val else ""

                headline_tag = card.select_one("a[data-review-title-typography='true']")
                headline = _clean(headline_tag.text) if headline_tag else ""

                comment_tag = card.select_one("p[data-service-review-text-typography='true']")
                comment_text = _clean(comment_tag.text) if comment_tag else ""

                rating_tag = card.select_one("div[data-service-review-rating]")
                stars = (
                    int(rating_tag["data-service-review-rating"])
                    if rating_tag and rating_tag.has_attr("data-service-review-rating")
                    else None
                )

                date_tag = card.select_one("time[data-service-review-date-time-ago='true']")
                review_date_absolute = (
                    date_tag["datetime"][:10]
                    if (date_tag and date_tag.has_attr("datetime"))
                    else None
                )

                reply_time_tag = card.select_one("div[class*='replyInfo'] time")
                response_date = (
                    reply_time_tag["datetime"][:10]
                    if (reply_time_tag and reply_time_tag.has_attr("datetime"))
                    else None
                )

                # FILTRE : on ignore les reviews totalement vides
                if not headline and not comment_text and stars is None:
                    # Pas de contenu exploitable -> on saute
                    continue

                review_id = f"{company_short}-{review_counter:05d}"
                review_counter += 1

                all_reviews.append(
                    {
                        "review_id": review_id,
                        "company_name": company_short.capitalize(),
                        "user_name": user_name,
                        "review_count": review_count,
                        "review_date_absolute": review_date_absolute,
                        "response_date": response_date,
                        "headline": headline,
                        "comment_text": comment_text,
                        "stars": stars,
                    }
                )

            # Petite pause entre les pages pour ne pas spammer
            time.sleep(random.uniform(1.5, 3.0))

    # Nom du fichier : YYYYMMDD.json 
    today = datetime.now().strftime("%Y%m%d")
    output_file = os.path.join(BASE_PATH, f"{today}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)

    print(f"[scrape_reviews] Fichier généré : {output_file}")
    print(f"[scrape_reviews] Nombre total de reviews extraites : {len(all_reviews)}")

    return output_file


@task
def update_scrape_window(current_window: str) -> str:
    """
    Avance la fenêtre de scraping dans WINDOW_ORDER
    et met à jour la Variable Airflow SCRAPE_WINDOW.
    Retourne la nouvelle fenêtre.
    """
    try:
        idx = WINDOW_ORDER.index(current_window)
    except ValueError:
        idx = 0

    next_window = WINDOW_ORDER[(idx + 1) % len(WINDOW_ORDER)]
    Variable.set("SCRAPE_WINDOW", next_window)
    print(
        f"[update_scrape_window] Fenêtre actuelle : {current_window} -> prochaine : {next_window}"
    )
    return next_window
