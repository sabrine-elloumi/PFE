import pandas as pd
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# === Configuration ===
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
    print("=" * 60)
    print("IMPORT FINAL DES CLIENTS (AVEC PROFILS)")
    print("=" * 60)

    # 1. Connexion à PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 2. Lire les clients bruts (sans en-tête)
    df_clients = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
    df_clients.columns = [
        'id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
        'first_name', 'identity', 'last_name', 'phone_number', 'uuid'
    ]

    # 3. Lire les profils (avec en-tête)
    df_stats = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')
    # Vérifier les colonnes nécessaires
    if 'client_id' not in df_stats.columns or 'profil' not in df_stats.columns:
        print("❌ Les colonnes 'client_id' ou 'profil' sont absentes de statistiques_clients.csv")
        print("Colonnes trouvées :", list(df_stats.columns))
        return

    # 4. Fusionner (inchangé)
    df = df_clients[['id', 'phone_number', 'first_name', 'last_name']].copy()
    df = df.merge(df_stats[['client_id', 'profil']], left_on='id', right_on='client_id', how='inner')
    print(f"{len(df)} clients avant dédoublonnage")

    # 5. Supprimer les doublons sur phone_number (garde le premier)
    df = df.drop_duplicates(subset=['phone_number'], keep='first')
    print(f"{len(df)} clients uniques après dédoublonnage")

    # 5. Hash du mot de passe
    hashed_pwd = hash_password(DEFAULT_PASSWORD)

    values = []
    for _, row in df.iterrows():
        # Nettoyer le numéro de téléphone
        phone = str(row['phone_number']).strip().replace('.0', '')
        if not phone.startswith('+'):
            phone = '+' + phone

        # Gérer les noms vides
        first = str(row['first_name']).strip() if pd.notna(row['first_name']) else ''
        last = str(row['last_name']).strip() if pd.notna(row['last_name']) else ''
        if first == '' and last == '':
            # Utiliser les 8 derniers caractères de l'ID pour un nom unique
            short_id = row['id'][-8:] if len(row['id']) >= 8 else row['id']
            first = f"Client_{short_id}"
            # last reste vide

        values.append((
            row['id'],
            phone,
            hashed_pwd,
            first[:100],
            last[:100],
            '',                         # email vide
            'USER',
            True,                       # actif
            'TND',
            datetime.now(),
            row['profil']               # profile_type
        ))

    # 6. Insertion en masse
    execute_values(cursor, """
        INSERT INTO users (id, phone_number, password, first_name, last_name, email,
                           role, active, preferred_currency, created_at, profile_type)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values)

    conn.commit()
    print(f"{len(values)} clients importés avec succès")

    cursor.close()
    conn.close()
    print("\n IMPORT TERMINÉ")

if __name__ == "__main__":
    main()