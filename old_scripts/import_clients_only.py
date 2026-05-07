import pandas as pd
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import uuid

STATS_CSV = "output/statistiques_clients.csv"

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

DEFAULT_PASSWORD = "passer123"

def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    print("=" * 60)
    print("IMPORT DES CLIENTS ET PROFILS")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    df = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')
    print(f"{len(df)} clients chargés")

    hashed_pwd = hash_password(DEFAULT_PASSWORD)

    values = []
    for _, row in df.iterrows():
        client_id = row['client_id']
        profil = row['profil']
        
        # Vérifier si l'ID est un UUID valide, sinon en générer un
        try:
            uuid.UUID(str(client_id))
        except ValueError:
            client_id = str(uuid.uuid4())
        
        values.append((
            str(client_id),
            f"+216{client_id[-8:]}" if len(str(client_id)) >= 8 else client_id,
            hashed_pwd,
            f"Client_{client_id[:8]}",
            "",
            "",
            'USER',
            True,
            'TND',
            datetime.now(),
            profil
        ))

    execute_values(cursor, """
        INSERT INTO users (id, phone_number, password, first_name, last_name, email,
                           role, active, preferred_currency, created_at, profile_type)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values)
    print(f"  {len(values)} clients importés")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n IMPORT CLIENTS TERMINÉ !")

if __name__ == "__main__":
    main()