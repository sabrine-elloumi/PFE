import pandas as pd
import bcrypt
import psycopg2
from datetime import datetime

CLIENTS_CSV = "output/clients_nettoyes.csv"
STATS_CSV = "output/statistiques_clients.csv"

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

DEFAULT_PASSWORD = "passer123"

def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Lire les clients
    df_clients = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
    df_clients.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
                          'first_name', 'identity', 'last_name', 'phone_number', 'uuid']

    # Lire les profils
    df_stats = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')

    # Fusionner
    df = df_clients[['id', 'phone_number', 'first_name', 'last_name']].copy()
    df = df.merge(df_stats[['client_id', 'profil']], left_on='id', right_on='client_id', how='inner')

    print(f"{len(df)} clients à importer")

    hashed = hash_password(DEFAULT_PASSWORD)

    count = 0
    for _, row in df.iterrows():
        phone = str(row['phone_number']).strip().replace('.0', '')
        if not phone.startswith('+'):
            phone = '+' + phone

        try:
            cursor.execute("""
                INSERT INTO users (id, phone_number, password, first_name, last_name, email,
                                   role, active, preferred_currency, created_at, profile_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['id'],
                phone,
                hashed,
                str(row['first_name'])[:100] if pd.notna(row['first_name']) else '',
                str(row['last_name'])[:100] if pd.notna(row['last_name']) else '',
                '',
                'USER',
                True,
                'TND',
                datetime.now(),
                row['profil']
            ))
            count += 1
            if count % 100 == 0:
                print(f"  {count} clients importés...")
        except Exception as e:
            print(f"Erreur pour {phone}: {e}")
            conn.rollback()  # Annule la transaction bloquée
            continue

    conn.commit()
    print(f"  {count} clients importés au total")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()