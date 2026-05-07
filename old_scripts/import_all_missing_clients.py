import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import bcrypt
from datetime import datetime
import uuid

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

STATS_CSV = "output/statistiques_clients.csv"
DEFAULT_PASSWORD = "passer123"

def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    print("=" * 60)
    print("IMPORT DE TOUS LES CLIENTS MANQUANTS")
    print("=" * 60)

    df = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')
    print(f"{len(df)} clients dans le fichier de stats")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Récupérer les IDs déjà présents dans users (rôle USER)
    cursor.execute("SELECT id FROM users WHERE role = 'USER'")
    existing_ids = {str(row[0]) for row in cursor.fetchall()}
    print(f"{len(existing_ids)} clients déjà présents dans la base")

    # Filtrer les clients manquants
    missing = df[~df['client_id'].isin(existing_ids)]
    print(f"{len(missing)} clients à importer")

    if missing.empty:
        print("Aucun client manquant. Fin du script.")
        return

    hashed_pwd = hash_password(DEFAULT_PASSWORD)
    values = []
    for _, row in missing.iterrows():
        client_id = row['client_id']
        # Générer un numéro de téléphone basé sur l'ID (pour que ce soit unique)
        phone = f"+216{client_id[-8:]}" if len(client_id) >= 8 else f"+216{client_id}"
        values.append((
            client_id,
            phone,
            hashed_pwd,
            f"Client_{client_id[:8]}",
            "",
            "",
            'USER',
            True,
            'TND',
            datetime.now(),
            row['profil']
        ))

    execute_values(cursor, """
        INSERT INTO users (id, phone_number, password, first_name, last_name, email,
                           role, active, preferred_currency, created_at, profile_type)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values, page_size=500)
    conn.commit()
    print(f"{len(values)} clients importés avec succès")

    cursor.close()
    conn.close()
    print("\n Tous les clients sont maintenant dans la base !")

if __name__ == "__main__":
    main()