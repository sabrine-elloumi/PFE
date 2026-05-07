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

def clean_phone(phone):
    """Nettoie le numéro de téléphone : le convertit en string et ajoute + si nécessaire"""
    if pd.isna(phone):
        return None
    s = str(phone).strip().replace('.0', '')
    if not s:
        return None
    if not s.startswith('+'):
        s = '+' + s
    return s

# ===================== LECTURE DES CLIENTS =====================
print(" Lecture des fichiers...")
df_clients = pd.read_csv(CLIENTS_CSV, sep=';', header=None, encoding='utf-8-sig')
df_clients.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
                      'first_name', 'identity', 'last_name', 'phone_number', 'uuid']

df_stats = pd.read_csv(STATS_CSV, sep=';', encoding='utf-8-sig')

# Fusion et dédoublonnage sur phone_number
df = df_clients[['id', 'phone_number', 'first_name', 'last_name']].copy()
df = df.merge(df_stats[['client_id', 'profil']], left_on='id', right_on='client_id', how='inner')
df['phone_number'] = df['phone_number'].apply(clean_phone)
df = df.dropna(subset=['phone_number'])
df = df.drop_duplicates(subset=['phone_number'], keep='first')

print(f" {len(df)} clients uniques à importer")

# ===================== PRÉPARATION DES TRANSACTIONS AVEC NUMÉRO =====================
print(" Enrichissement des transactions avec le numéro de téléphone...")
df_trans = pd.read_csv(TRANSACTIONS_CSV, sep=';', decimal=',', encoding='utf-8-sig')

# Vérifier la colonne client_id
if 'client_id' not in df_trans.columns:
    print(" La colonne 'client_id' est absente du CSV des transactions.")
    exit(1)

# Préparer un mapping client_id -> phone_number à partir de df_clients (avant dédoublonnage)
df_clients_phone = df_clients[['id', 'phone_number']].copy()
df_clients_phone['phone_number'] = df_clients_phone['phone_number'].apply(clean_phone)
df_clients_phone = df_clients_phone.dropna(subset=['phone_number'])

# Joindre les transactions pour obtenir le numéro
df_trans = df_trans.merge(df_clients_phone, left_on='client_id', right_on='id', how='left')
df_trans = df_trans.dropna(subset=['phone_number'])
print(f"   {len(df_trans)} transactions conservées (avec numéro de téléphone)")

if df_trans.empty:
    print(" Aucune transaction avec numéro valide.")
    exit(1)

# ===================== CONNEXION POSTGRESQL =====================
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# 1. Supprimer les anciens utilisateurs non admin
print("  Suppression des anciens utilisateurs (sauf admin)...")
cursor.execute("DELETE FROM users WHERE role != 'ADMIN'")
print(f"   {cursor.rowcount} utilisateurs supprimés")
conn.commit()

# 2. Insérer les clients dédoublonnés
hashed_pwd = hash_password(DEFAULT_PASSWORD)
values_users = []
for _, row in df.iterrows():
    # Générer un UUID si l'ID n'est pas valide
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

# 3. Mapping phone_number -> user_id (après insertion)
cursor.execute("SELECT id, phone_number FROM users WHERE role = 'USER'")
phone_to_user_id = {row[1]: row[0] for row in cursor.fetchall()}
print(f" {len(phone_to_user_id)} utilisateurs mappés par numéro")

# ===================== IMPORT DES TRANSACTIONS =====================
print(" Import des transactions...")

df_trans['transaction_date'] = pd.to_datetime(df_trans['transaction_date'], errors='coerce')
df_trans = df_trans.dropna(subset=['transaction_date', 'amount'])
df_trans = df_trans[df_trans['amount'] > 0]

if 'description' not in df_trans.columns:
    df_trans['description'] = df_trans.get('reference', 'Transaction historique').fillna('')
else:
    df_trans['description'] = df_trans['description'].fillna('Transaction historique')

# Récupérer ou créer la catégorie "Autre"
cursor.execute("SELECT id FROM categories WHERE name = 'Autre' LIMIT 1")
row = cursor.fetchone()
if not row:
    autre_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO categories (id, name, icon, color, is_system)
        VALUES (%s, 'Autre', 'category', '#64748B', true)
    """, (autre_id,))
    conn.commit()
else:
    autre_id = row[0]

# Préparer les valeurs des transactions
values_trans = []
for _, row in df_trans.iterrows():
    phone = row['phone_number']
    user_id = phone_to_user_id.get(phone)
    if user_id is None:
        # Normalement ne devrait pas arriver
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
    print(" Aucune transaction correspondante")

cursor.close()
conn.close()
print("\n IMPORT TERMINÉ AVEC SUCCÈS !")