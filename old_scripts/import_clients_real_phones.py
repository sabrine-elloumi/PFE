import pandas as pd
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
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

def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    print("=" * 60)
    print("REMPLACEMENT DES CLIENTS AVEC VRAIS NUMÉROS")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1. Supprimer tous les clients non-admin (conserver l'admin)
    print("Suppression des anciens clients (sauf admin)...")
    cursor.execute("DELETE FROM users WHERE role != 'ADMIN'")
    print(f"  {cursor.rowcount} clients supprimés")

    # 2. Lire les vrais clients
    df_clients = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
    df_clients.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
                          'first_name', 'identity', 'last_name', 'phone_number', 'uuid']
    
    df_stats = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')
    df = df_clients[['id', 'phone_number', 'first_name', 'last_name']].copy()
    df = df.merge(df_stats[['client_id', 'profil']], left_on='id', right_on='client_id', how='inner')
    
    print(f"{len(df)} clients avec vrais numéros chargés")

    hashed_pwd = hash_password(DEFAULT_PASSWORD)

    values = []
    for _, row in df.iterrows():
        phone = str(row['phone_number']).strip()
        if not phone.startswith('+'):
            phone = '+' + phone
        # Nettoyer le numéro (enlever .0 si présent)
        phone = phone.replace('.0', '')
        
        values.append((
            row['id'],
            phone,
            hashed_pwd,
            str(row['first_name']) if pd.notna(row['first_name']) else '',
            str(row['last_name']) if pd.notna(row['last_name']) else '',
            '',
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
    """, values)
    print(f"  {len(values)} clients importés avec vrais numéros")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n IMPORT CLIENTS TERMINÉ !")

if __name__ == "__main__":
    main()