import os
import pandas as pd
import psycopg2
import hashlib
from airflow.decorators import task

# =====================================================================
# ============= CONNEXION POSTGRESQL (via .env uniquement)=============
# =====================================================================
def _get_db_connection():
    """
    Retourne une connexion PostgreSQL en utilisant
    uniquement POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    et POSTGRES_HOST / POSTGRES_PORT si présents.
    """
    host = os.environ.get("POSTGRES_HOST", "postgres_metadata")
    port = os.environ.get("POSTGRES_PORT", "5432")

    dbname = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]

    return psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )

# =====================================================================
# ============= CALCUL HASH FICHIER (détection changements) ============
# =====================================================================
def _file_hash(path):
    """
    Retourne un hash SHA-256 représentant l’état du CSV.
    Permet de détecter si le fichier a changé.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

# =====================================================================
# ============= NETTOYAGE ADRESSE =====================================
# =====================================================================
def _split_address(addr: str):
    """
    Exemples :
    "12 Rue de Paris" -> ("12", "Rue de Paris")
    "Rue de la Paix"  -> (None, "Rue de la Paix")
    """
    if not isinstance(addr, str) or not addr.strip():
        return None, None

    parts = addr.split()

    if parts[0].isdigit():
        return parts[0], " ".join(parts[1:])

    return None, addr

# =====================================================================
# ============= CONVERSION POURCENTAGE ================================
# =====================================================================
def _pct(value):
    """
    Convertit "38%", "<1%", " <1 " en float.
    <1% devient 0.5 par convention.
    """
    if value is None or pd.isna(value):
        return None

    s = str(value).strip().replace(",", ".").replace("%", "")

    if "<" in s:
        return 0.5

    if not s.replace(".", "", 1).isdigit():
        return None

    return float(s)

# =====================================================================
# ============= TÂCHE 1 : Création des tables =========================
# =====================================================================
@task
def create_metadata_tables():
    """
    Crée les tables nécessaires.
    """
    conn = _get_db_connection()
    cur = conn.cursor()

    # CATEGORY
    cur.execute("""
        CREATE TABLE IF NOT EXISTS category (
            category_id SERIAL PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL
        );
    """)

    # ENTREPRISE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entreprise (
            entreprise_id TEXT PRIMARY KEY,
            entreprise_name TEXT,
            email TEXT,
            phone TEXT,
            web_site TEXT,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES category(category_id)
        );
    """)

    # ADRESS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS adress (
            entreprise_id TEXT PRIMARY KEY REFERENCES entreprise(entreprise_id),
            street_number TEXT,
            street_name TEXT,
            zip_code TEXT,
            city TEXT,
            country TEXT
        );
    """)

    # RATING
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rating (
            entreprise_id TEXT PRIMARY KEY REFERENCES entreprise(entreprise_id),
            one_star NUMERIC,
            two_star NUMERIC,
            three_star NUMERIC,
            four_star NUMERIC,
            five_star NUMERIC
        );
    """)

    # TABLE POUR STOCKER LE HASH DU FICHIER
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata_file_state (
            id SERIAL PRIMARY KEY,
            file_hash TEXT UNIQUE NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

    return "tables_created"

# =====================================================================
# ============= TÂCHE 2 : Chargement des métadonnées ==================
# =====================================================================
@task
def load_company_metadata_to_postgres(csv_path: str):
    """
    Charge les métadonnées du CSV uniquement si le fichier a changé.
    Skip automatique si hash identique.
    """
    conn = _get_db_connection()
    cur = conn.cursor()

    # -----------------------------------------------------------------
    # 1) Calcul hash actuel
    # -----------------------------------------------------------------
    current_hash = _file_hash(csv_path)

    # Lire le hash stocké (si existe)
    cur.execute("SELECT file_hash FROM metadata_file_state LIMIT 1;")
    row = cur.fetchone()

    # Comparaison — skip si inchangé
    if row and row[0] == current_hash:
        print("✔ Métadonnées inchangées — SKIP du chargement.")
        cur.close()
        conn.close()
        return "no_change"

    print("Nouveau fichier détecté — chargement nécessaire.")

    # -----------------------------------------------------------------
    # 2) Lecture CSV
    # -----------------------------------------------------------------
    df = pd.read_csv(csv_path)

    # -----------------------------------------------------------------
    # 3) CATEGORY
    # -----------------------------------------------------------------
    for cat in df["category"].dropna().unique():
        cur.execute("""
            INSERT INTO category (category_name)
            VALUES (%s)
            ON CONFLICT (category_name) DO NOTHING;
        """, (cat,))

    cur.execute("SELECT category_id, category_name FROM category;")
    category_map = {name: cid for cid, name in cur.fetchall()}

    # -----------------------------------------------------------------
    # 4) ENTREPRISE
    # -----------------------------------------------------------------
    for _, row in df.iterrows():
        entreprise_id = str(row["id"])
        entreprise_name = row["displayName"]
        email = row["email"]
        phone = row["phone"]
        website = row["websiteUrl"]
        category_id = category_map[row["category"]]

        cur.execute("""
            INSERT INTO entreprise (entreprise_id, entreprise_name, email, phone, web_site, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (entreprise_id) DO UPDATE
            SET entreprise_name = EXCLUDED.entreprise_name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                web_site = EXCLUDED.web_site,
                category_id = EXCLUDED.category_id;
        """, (
            entreprise_id, entreprise_name, email, phone, website, category_id
        ))

    # -----------------------------------------------------------------
    # 5) ADRESS
    # -----------------------------------------------------------------
    for _, row in df.iterrows():
        entreprise_id = str(row["id"])
        street_nb, street_name = _split_address(row.get("address"))

        cur.execute("""
            INSERT INTO adress (entreprise_id, street_number, street_name, zip_code, city, country)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (entreprise_id) DO UPDATE
            SET street_number = EXCLUDED.street_number,
                street_name = EXCLUDED.street_name,
                zip_code = EXCLUDED.zip_code,
                city = EXCLUDED.city,
                country = EXCLUDED.country;
        """, (
            entreprise_id, street_nb, street_name,
            row["zipCode"], row["city"], row["country"]
        ))

    # -----------------------------------------------------------------
    # 6) RATING
    # -----------------------------------------------------------------
    for _, row in df.iterrows():
        entreprise_id = str(row["id"])

        cur.execute("""
            INSERT INTO rating (entreprise_id, one_star, two_star, three_star, four_star, five_star)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (entreprise_id) DO UPDATE
            SET one_star = EXCLUDED.one_star,
                two_star = EXCLUDED.two_star,
                three_star = EXCLUDED.three_star,
                four_star = EXCLUDED.four_star,
                five_star = EXCLUDED.five_star;
        """, (
            entreprise_id,
            _pct(row["one_star_percentage"]),
            _pct(row["two_star_percentage"]),
            _pct(row["three_star_percentage"]),
            _pct(row["four_star_percentage"]),
            _pct(row["five_star_percentage"])
        ))

    # -----------------------------------------------------------------
    # 7) Mise à jour du hash référent
    # -----------------------------------------------------------------
    cur.execute("DELETE FROM metadata_file_state;")
    cur.execute(
        "INSERT INTO metadata_file_state (file_hash) VALUES (%s);",
        (current_hash,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return "metadata_loaded"
