import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid
import os

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

CSV_PATH = "output/transactions_clients.csv"
PROVIDERS_CSV = "output/providers_nettoyes.csv"

# Mapping operation_type -> (type, catégorie)
OP_TYPE_MAPPING = {
    1.0:   ('INCOME', 'Recharge Téléphone'),
    2.0:   ('INCOME', 'Recharge Téléphone'),
    3.0:   ('INCOME', 'Recharge Téléphone'),
    1002.0: ('EXPENSE', 'Paiement Factures'),
    1004.0: ('EXPENSE', 'Transfert'),
    1005.0: ('EXPENSE', 'Paiement Marchand'),
    1006.0: ('EXPENSE', 'Autre'),
    5007.0: ('EXPENSE', 'Frais'),
    5009.0: ('EXPENSE', 'Commission'),
}

PROVIDER_CAT_MAPPING = {
    'SONEDE':  'Eau',
    'STEG':    'Électricité',
    'TOPNET':  'Internet',
    'BEE':     'Internet',
    'OOREDOO': 'Téléphonie',
    'ORANGE':  'Téléphonie',
    'TT':      'Téléphonie',
    'CNTE':    'Éducation',
}

DEFAULT_CAT = 'Autre'

SYSTEM_CATEGORIES = [
    ('Revenu', 'attach_money', '#10B981'),  # catégorie générique
    ('Recharge Téléphone', 'phone_android', '#F59E0B'),
    ('Paiement Factures', 'receipt', '#3B82F6'),
    ('Transfert', 'swap_horiz', '#8B5CF6'),
    ('Paiement Marchand', 'shopping_cart', '#EC4899'),
    ('Frais', 'money_off', '#EF4444'),
    ('Commission', 'percent', '#F59E0B'),
    ('Eau', 'water_drop', '#3B82F6'),
    ('Électricité', 'bolt', '#F59E0B'),
    ('Internet', 'wifi', '#8B5CF6'),
    ('Téléphonie', 'phone_iphone', '#EC4899'),
    ('Éducation', 'school', '#10B981'),
]

def get_or_create_category(cursor, name, icon='category', color='#64748B'):
    cursor.execute("SELECT id FROM categories WHERE name = %s AND is_system = true", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cat_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO categories (id, name, icon, color, is_system, created_at)
        VALUES (%s, %s, %s, %s, true, NOW())
    """, (cat_id, name, icon, color))
    return cat_id

def main():
    print("=" * 70)
    print("CORRECTION DES TRANSACTIONS (avec revenus détectés)")
    print("=" * 70)

    # Lecture CSV
    print(" Lecture des transactions...")
    df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
    print(f"   {len(df)} transactions chargées")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Création des catégories
    print(" Création des catégories...")
    cat_ids = {}
    for name, icon, color in SYSTEM_CATEGORIES:
        cat_ids[name] = get_or_create_category(cursor, name, icon, color)
    cat_ids[DEFAULT_CAT] = get_or_create_category(cursor, DEFAULT_CAT, 'category', '#64748B')
    conn.commit()
    print(f"   {len(cat_ids)} catégories disponibles")

    # Chargement providers
    provider_title = {}
    if os.path.exists(PROVIDERS_CSV):
        df_prov = pd.read_csv(PROVIDERS_CSV, sep=';', encoding='utf-8-sig')
        # Trouver la colonne id et title
        id_col = None
        title_col = None
        for col in df_prov.columns:
            if 'id' in col.lower():
                id_col = col
            if 'title' in col.lower() or 'name' in col.lower() or 'nom' in col.lower():
                title_col = col
        if id_col and title_col:
            provider_title = dict(zip(df_prov[id_col].astype(str), df_prov[title_col].astype(str)))
            print(f"   Mapping fournisseurs : {len(provider_title)} entrées")
        else:
            print("   Colonnes id/title non trouvées dans providers_nettoyes.csv")
    else:
        print("   providers_nettoyes.csv non trouvé – catégorisation basée sur operation_type uniquement")

    updates = []
    for _, row in df.iterrows():
        tx_id = row['id']
        op_type = row.get('operation_type')
        provider_id = str(row.get('provider_id')) if pd.notna(row.get('provider_id')) else None

        new_type = None
        cat_name = None

        # Priorité : operation_type
        if op_type is not None and op_type in OP_TYPE_MAPPING:
            new_type, cat_name = OP_TYPE_MAPPING[op_type]
        else:
            # Fallback : dépense, catégorie Autre
            new_type = 'EXPENSE'
            cat_name = DEFAULT_CAT

        # Si on a un provider et qu'il est connu, on peut affiner la catégorie (uniquement pour les dépenses)
        if provider_id and provider_id in provider_title and new_type == 'EXPENSE':
            title = provider_title[provider_id]
            for key, cat in PROVIDER_CAT_MAPPING.items():
                if key in title.upper():
                    cat_name = cat
                    break

        category_id = cat_ids.get(cat_name, cat_ids[DEFAULT_CAT])
        updates.append((tx_id, new_type, category_id))

    print(f" {len(updates)} transactions à mettre à jour")

    if updates:
        execute_values(cursor, """
            UPDATE transactions
            SET type = data.type::text,
                category_id = data.category_id::uuid
            FROM (VALUES %s) AS data(id, type, category_id)
            WHERE transactions.id = data.id::uuid
        """, updates, page_size=1000)
        conn.commit()
        print(" Mise à jour terminée")

    # Récapitulatif
    cursor.execute("SELECT type, COUNT(*) FROM transactions GROUP BY type")
    print("\n Types après correction :")
    for t, cnt in cursor.fetchall():
        print(f"   {t} : {cnt}")

    cursor.execute("""
        SELECT c.name, COUNT(*)
        FROM transactions t JOIN categories c ON t.category_id = c.id
        GROUP BY c.name
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    print("\n Top 10 catégories :")
    for cat, cnt in cursor.fetchall():
        print(f"   {cat:<25} : {cnt:5}")

    cursor.close()
    conn.close()
    print("\n TERMINÉ !")

if __name__ == "__main__":
    main()