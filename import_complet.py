import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import uuid
import bcrypt

# ===================== CONFIGURATION =====================
CLIENTS_CSV = "output/clients_nettoyes.csv"
STATS_CSV = "output/statistiques_clients.csv"
TRANSACTIONS_CSV = "output/transactions_clients.csv"

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

# ===================== LECTURE DES CLIENTS =====================
print(" Lecture des fichiers...")
df_clients = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
df_clients.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
                      'first_name', 'identity', 'last_name', 'phone_number', 'uuid']

df_stats = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')

# Fusion et dédoublonnage sur phone_number (garde la première occurrence)
df = df_clients[['id', 'phone_number', 'first_name', 'last_name']].copy()
df = df.merge(df_stats[['client_id', 'profil']], left_on='id', right_on='client_id', how='inner')
df = df.drop_duplicates(subset=['phone_number'], keep='first')

# Nettoyage du numéro de téléphone
df['phone_number'] = df['phone_number'].astype(str).str.strip().str.replace('.0', '', regex=False)
df['phone_number'] = df['phone_number'].apply(lambda x: x if x.startswith('+') else '+' + x)

print(f" {len(df)} clients uniques à importer")

# ===================== CONNEXION POSTGRESQL =====================
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# 1. Supprimer tous les utilisateurs non administrateurs (pour repartir propre)
print("  Suppression des anciens utilisateurs (sauf admin)...")
cursor.execute("DELETE FROM users WHERE role != 'ADMIN'")
print(f"   {cursor.rowcount} utilisateurs supprimés")
conn.commit()

# 2. Préparer et insérer les clients
hashed_pwd = hash_password(DEFAULT_PASSWORD)
values_users = []
for _, row in df.iterrows():
    # Générer un UUID valide si l'ID n'est pas un UUID
    try:
        uuid.UUID(str(row['id']))
        client_id = row['id']
    except ValueError:
        client_id = str(uuid.uuid4())
    
    values_users.append((
        client_id,
        row['phone_number'],
        hashed_pwd,
        str(row['first_name'])[:100] if pd.notna(row['first_name']) else '',
        str(row['last_name'])[:100] if pd.notna(row['last_name']) else '',
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
""", values_users, page_size=1000)
conn.commit()
print(f" {len(values_users)} clients insérés")

# 3. Récupérer les ID des clients insérés (pour mapper les transactions)
cursor.execute("SELECT id, phone_number FROM users WHERE role = 'USER'")
rows = cursor.fetchall()
user_map = {row[1]: row[0] for row in rows}
print(f" {len(user_map)} utilisateurs mappés par numéro de téléphone")

# ===================== IMPORT DES TRANSACTIONS =====================
print(" Import des transactions...")
df_trans = pd.read_csv(TRANSACTIONS_CSV, sep=';', decimal=',', encoding='utf-8-sig')

# Vérifier colonnes nécessaires
required_cols = ['client_id', 'amount', 'transaction_date']
if not all(c in df_trans.columns for c in required_cols):
    print(" Colonnes manquantes dans transactions_clients.csv")
    print(f"   Colonnes trouvées : {list(df_trans.columns)}")
    exit(1)

# Nettoyer la date
df_trans['transaction_date'] = pd.to_datetime(df_trans['transaction_date'], errors='coerce')
df_trans = df_trans.dropna(subset=['client_id', 'amount', 'transaction_date'])
df_trans = df_trans[df_trans['amount'] > 0]

# Colonne description : utiliser 'description' si elle existe, sinon 'reference'
if 'description' not in df_trans.columns:
    df_trans['description'] = df_trans.get('reference', 'Transaction historique').fillna('')
else:
    df_trans['description'] = df_trans['description'].fillna('Transaction historique')

# Récupérer l'ID de la catégorie "Autre"
cursor.execute("SELECT id FROM categories WHERE name = 'Autre' LIMIT 1")
row = cursor.fetchone()
if not row:
    print(" Catégorie 'Autre' introuvable. Création automatique...")
    autre_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO categories (id, name, icon, color, is_system)
        VALUES (%s, 'Autre', 'category', '#64748B', true)
    """, (autre_id,))
    conn.commit()
else:
    autre_id = row[0]

# Récupérer la liste des users_id existants (pour vérifier rapidement)
cursor.execute("SELECT id FROM users")
existing_user_ids = {str(row[0]) for row in cursor.fetchall()}

# Préparer les valeurs des transactions
values_trans = []
for _, row in df_trans.iterrows():
    user_id = str(row['client_id'])
    if user_id not in existing_user_ids:
        print(f" Client {user_id[:8]}... non trouvé, transaction ignorée")
        continue
    
    values_trans.append((
        str(uuid.uuid4()),
        user_id,
        float(row['amount']),
        str(row['description'])[:255],
        'EXPENSE',
        row['transaction_date'],
        autre_id,
        None,
        None,
        False,
        False,
        datetime.now(),
        datetime.now()
    ))

if values_trans:
    execute_values(cursor, """
        INSERT INTO transactions (id, user_id, amount, description, type, transaction_date,
                                  category_id, ai_predicted_category, ai_confidence,
                                  is_anomaly, is_recurring, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values_trans, page_size=500)
    conn.commit()
    print(f" {len(values_trans)} transactions importées")
else:
    print(" Aucune transaction à importer (vérifiez les correspondances client_id)")

cursor.close()
conn.close()
print("\n IMPORT TERMINÉ AVEC SUCCÈS !")