import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

MAPPING = {
    1.0: ('Recharge Téléphone', 'EXPENSE'),
    2.0: ('Recharge Téléphone', 'EXPENSE'),
    3.0: ('Recharge Téléphone', 'EXPENSE'),
    1002.0: ('Paiement Factures', 'EXPENSE'),
    1004.0: ('Transfert', 'EXPENSE'),
    1005.0: ('Paiement Marchand', 'EXPENSE'),
    1006.0: ('Autre', 'EXPENSE'),
    5007.0: ('Frais', 'EXPENSE'),
    5009.0: ('Commission', 'EXPENSE'),
}

print(" Lecture du CSV transactions...")
df = pd.read_csv("output/transactions_clients.csv", sep=';', decimal=',', encoding='utf-8-sig')

if 'operation_type' not in df.columns:
    print(" Colonne 'operation_type' absente")
    exit(1)

df['operation_type'] = df['operation_type'].where(pd.notna(df['operation_type']), None)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("SELECT name, id FROM categories WHERE is_system = true")
cat_map = {row[0]: row[1] for row in cursor.fetchall()}

for cat_name, _ in MAPPING.values():
    if cat_name not in cat_map:
        print(f" Catégorie '{cat_name}' manquante. Création automatique...")
        new_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO categories (id, name, icon, color, is_system, created_at)
            VALUES (%s, %s, 'category', '#64748B', true, NOW())
        """, (new_id, cat_name))
        conn.commit()
        cat_map[cat_name] = new_id

updates = []
for _, row in df.iterrows():
    op_type = row['operation_type']
    if pd.isna(op_type):
        continue
    cat_name, _ = MAPPING.get(op_type, ('Autre', 'EXPENSE'))
    category_id = cat_map.get(cat_name)
    if category_id:
        updates.append((row['id'], category_id))

print(f"🔧 {len(updates)} transactions à mettre à jour")

if updates:
    execute_values(cursor, """
        UPDATE transactions
        SET category_id = data.category_id::uuid
        FROM (VALUES %s) AS data(id, category_id)
        WHERE transactions.id = data.id::uuid
    """, updates, page_size=1000)
    conn.commit()
    print(" Mise à jour des catégories terminée")
else:
    print(" Aucune transaction à mettre à jour")

cursor.close()
conn.close()