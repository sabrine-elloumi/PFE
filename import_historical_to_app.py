import pandas as pd
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import uuid

# =============================================
# CHEMINS DES CSV (à adapter si nécessaire)
# =============================================
CLIENTS_CSV = "output/clients_nettoyes.csv"
TRANSACTIONS_CSV = "output/transactions_clients.csv"
STATS_CSV = "output/statistiques_clients.csv"
RECOMMENDATIONS_CSV = "output/recommandations_clients.csv"

# =============================================
# CONNEXION À LA BASE (port 5433)
# =============================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

DEFAULT_PASSWORD = "passer123"

# =============================================
# FONCTIONS
# =============================================
def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_or_create_autre_category(cursor):
    # Note : la table s'appelle "categories" (pluriel)
    cursor.execute("SELECT id FROM categories WHERE name = 'Autre' LIMIT 1")
    row = cursor.fetchone()
    if row:
        return row[0]
    autre_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO categories (id, name, icon, color, is_system)
        VALUES (%s, 'Autre', 'category', '#64748B', true)
    """, (autre_id,))
    return autre_id

def import_clients(cursor):
    print("--- Import des clients ---")
    df = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
    df.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
                  'first_name', 'identity', 'last_name', 'phone_number', 'uuid']
    df['first_name'] = df['first_name'].fillna('')
    df['last_name'] = df['last_name'].fillna('')
    df['email'] = ''
    df['create_date_time'] = pd.to_datetime(df['create_date_time'], errors='coerce')
    df['create_date_time'] = df['create_date_time'].fillna(datetime.now())

    hashed_pwd = hash_password(DEFAULT_PASSWORD)

    values = []
    for _, row in df.iterrows():
        values.append((
            row['id'],
            row['phone_number'],
            hashed_pwd,
            row['first_name'],
            row['last_name'],
            row['email'],
            'USER',
            True,
            'TND',
            row['create_date_time'],
            None
        ))

    execute_values(cursor, """
        INSERT INTO users (id, phone_number, password, first_name, last_name, email,
                           role, active, preferred_currency, created_at, profile_type)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values)
    print(f"  {len(values)} clients importés")

def import_transactions(cursor, autre_cat_id):
    print("--- Import des transactions ---")
    df = pd.read_csv(TRANSACTIONS_CSV, sep=';', decimal=',', encoding='utf-8-sig')
    if 'description' not in df.columns:
        df['description'] = df.get('reference', 'Transaction historique').fillna('')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df = df.dropna(subset=['client_id', 'amount', 'transaction_date'])
    df = df[df['amount'] > 0]

    values = []
    for _, row in df.iterrows():
        values.append((
            str(uuid.uuid4()),
            row['client_id'],
            row['amount'],
            row['description'][:255] if isinstance(row['description'], str) else '',
            'EXPENSE',
            row['transaction_date'],
            autre_cat_id,
            None,
            None,
            False,
            False,
            datetime.now(),
            datetime.now()
        ))

    execute_values(cursor, """
        INSERT INTO transaction (id, user_id, amount, description, type, transaction_date,
                                 category_id, ai_predicted_category, ai_confidence,
                                 is_anomaly, is_recurring, created_at, updated_at)
        VALUES %s
    """, values, page_size=1000)
    print(f"  {len(values)} transactions importées")

def update_profiles(cursor):
    print("--- Mise à jour des profils ---")
    df = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')
    count = 0
    for _, row in df.iterrows():
        cursor.execute(
            "UPDATE users SET profile_type = %s, profile_updated_at = NOW() WHERE id = %s",
            (row['profil'], row['client_id'])
        )
        count += cursor.rowcount
    print(f"  {count} utilisateurs mis à jour")

def import_recommendations(cursor):
    print("--- Import des recommandations ---")
    df = pd.read_csv(RECOMMENDATIONS_CSV, sep=';', encoding='utf-8-sig')
    df_unique = df.drop_duplicates(subset=['profil'])
    count = 0
    for _, row in df_unique.iterrows():
        cursor.execute("""
            INSERT INTO profile_recommendations (profil, recommendation_1, recommendation_2,
                                                 recommendation_3, recommendation_alert)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (profil) DO UPDATE SET
                recommendation_1 = EXCLUDED.recommendation_1,
                recommendation_2 = EXCLUDED.recommendation_2,
                recommendation_3 = EXCLUDED.recommendation_3,
                recommendation_alert = EXCLUDED.recommendation_alert
        """, (
            row['profil'],
            row['recommendation_1'],
            row['recommendation_2'],
            row['recommendation_3'],
            row['recommendation_alert']
        ))
        count += 1
    print(f"  {count} recommandations importées")

def main():
    print("=" * 60)
    print("IMPORT DES DONNÉES HISTORIQUES")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    autre_cat_id = get_or_create_autre_category(cursor)
    print(f"Catégorie 'Autre' : {autre_cat_id}")

    import_clients(cursor)
    import_transactions(cursor, autre_cat_id)
    update_profiles(cursor)
    import_recommendations(cursor)

    conn.commit()
    cursor.close()
    conn.close()

    print("\n IMPORT TERMINÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    main()