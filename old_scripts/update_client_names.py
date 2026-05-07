import pandas as pd
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

CLIENTS_CSV = "output/clients_nettoyes.csv"

print(" Lecture du CSV clients...")

# Lire le CSV en forçant la colonne phone_number (colonne 8) comme string
df = pd.read_csv(
    CLIENTS_CSV, 
    sep=';', 
    header=None, 
    encoding='utf-8-sig',
    dtype={8: str}  # la colonne phone_number est la 9ème (index 8)
)
df.columns = ['id', 'created_by', 'create_date_time', 'modified_by', 'modified_date_time',
              'first_name', 'identity', 'last_name', 'phone_number', 'uuid']

# Nettoyer les numéros (enlever .0, espaces, etc.)
def clean_phone(phone):
    if pd.isna(phone):
        return ''
    phone = str(phone).strip()
    if phone == '' or phone == 'nan' or phone == 'None':
        return ''
    phone = phone.replace('.0', '')
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

df['phone_number'] = df['phone_number'].apply(clean_phone)
df = df[df['phone_number'] != '']

# Noms
df['first_name'] = df['first_name'].fillna('').astype(str)
df['last_name'] = df['last_name'].fillna('').astype(str)

# Générer un prénom par défaut si vide
df['first_name'] = df.apply(
    lambda r: r['first_name'] if r['first_name'] else f"Client_{r['phone_number'][-4:]}",
    axis=1
)

print(f" {len(df)} clients à mettre à jour")

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

updated = 0
for _, row in df.iterrows():
    cursor.execute("""
        UPDATE users
        SET first_name = %s, last_name = %s
        WHERE phone_number = %s AND role = 'USER'
    """, (row['first_name'], row['last_name'], row['phone_number']))
    updated += cursor.rowcount

conn.commit()
print(f" {updated} utilisateurs mis à jour")

cursor.close()
conn.close()