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

CSV_PATH = "output/transactions_clients.csv"

# Mapping operation_type -> (type, catégorie)
OP_TYPE_MAPPING = {
    1.0:   ('EXPENSE', 'Recharge Téléphone'),
    2.0:   ('EXPENSE', 'Recharge Téléphone'),
    3.0:   ('EXPENSE', 'Recharge Téléphone'),
    1002.0: ('EXPENSE', 'Paiement Factures'),
    1004.0: ('EXPENSE', 'Transfert'),
    1005.0: ('EXPENSE', 'Paiement Marchand'),
    1006.0: ('EXPENSE', 'Autre'),
    5007.0: ('EXPENSE', 'Frais'),
    5009.0: ('EXPENSE', 'Commission'),
    '0001': ('INCOME', 'Revenu'),
    '0002': ('INCOME', 'Revenu'),
    '0003': ('INCOME', 'Revenu'),
    'UL':   ('EXPENSE', 'Cash Out'),
    'N1':   ('INCOME', 'Cash In'),
    'N3':   ('INCOME', 'Cash In'),
    'PS':   ('EXPENSE', 'Paiement Factures'),
    'ST':   ('EXPENSE', 'Paiement Factures'),
    'EN':   ('EXPENSE', 'Paiement Factures'),
    'RA':   ('EXPENSE', 'Transfert International'),
    'RD':   ('EXPENSE', 'Transfert International'),
}

# Mapping provider (à partir du titre) -> (type, catégorie)
PROVIDER_MAPPING = {
    'SONEDE':          ('EXPENSE', 'Eau'),
    'STEG':            ('EXPENSE', 'Électricité'),
    'TOPNET':          ('EXPENSE', 'Internet'),
    'BEE':             ('EXPENSE', 'Internet'),
    'OOREDOO':         ('EXPENSE', 'Téléphonie'),
    'ORANGE':          ('EXPENSE', 'Téléphonie'),
    'TT':              ('EXPENSE', 'Téléphonie'),
    'CNTE':            ('EXPENSE', 'Éducation'),
}

DEFAULT_CAT = 'Autre'

SYSTEM_CATEGORIES = [
    ('Revenu', 'attach_money', '#10B981'),
    ('Recharge Téléphone', 'phone_android', '#F59E0B'),
    ('Paiement Factures', 'receipt', '#3B82F6'),
    ('Transfert', 'swap_horiz', '#8B5CF6'),
    ('Paiement Marchand', 'shopping_cart', '#EC4899'),
    ('Frais', 'money_off', '#EF4444'),
    ('Commission', 'percent', '#F59E0B'),
    ('Cash Out', 'money_off', '#EF4444'),
    ('Cash In', 'attach_money', '#10B981'),
    ('Transfert International', 'public', '#06B6D4'),
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
    print("=" * 60)
    print("CORRECTION DES TRANSACTIONS (TYPE + CATÉGORIE) DEPUIS LE CSV")
    print("=" * 60)

    # 1. Lire le CSV
    print(" Lecture du CSV transactions...")
    df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
    required_cols = ['id', 'client_id', 'amount', 'transaction_date']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f" Colonnes manquantes dans le CSV : {missing}")
        return
    print(f"   {len(df)} transactions chargées")

    # 2. Connexion DB
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 3. Créer les catégories
    print(" Création des catégories système...")
    cat_ids = {}
    for name, icon, color in SYSTEM_CATEGORIES:
        cat_ids[name] = get_or_create_category(cursor, name, icon, color)
    cat_ids[DEFAULT_CAT] = get_or_create_category(cursor, DEFAULT_CAT, 'category', '#64748B')
    conn.commit()
    print(f"   {len(cat_ids)} catégories disponibles")

    # 4. Charger le mapping provider (optionnel)
    provider_map = {}
    try:
        df_providers = pd.read_csv("output/providers_nettoyes.csv", sep=';', encoding='utf-8-sig')
        if 'id' in df_providers.columns and 'title' in df_providers.columns:
            provider_map = dict(zip(df_providers['id'].astype(str), df_providers['title'].astype(str)))
        print(f"   Mapping fournisseurs chargé : {len(provider_map)} entrées")
    except:
        print("   Aucun fichier providers_nettoyes.csv trouvé, mapping provider ignoré")

    # 5. Déterminer type et catégorie pour chaque transaction
    updates = []  # (id, new_type, category_id)
    for _, row in df.iterrows():
        tx_id = row['id']
        op_type = row.get('operation_type')
        provider_id = str(row.get('provider_id')) if pd.notna(row.get('provider_id')) else None
        receiver_id = row.get('receiver_id') if pd.notna(row.get('receiver_id')) else None

        new_type = None
        cat_name = None

        # Règle 1 : receiver_id non null -> revenu (transfert reçu)
        if receiver_id is not None:
            new_type = 'INCOME'
            cat_name = 'Transfert'
        else:
            # Règle 2 : operation_type
            if op_type is not None and op_type in OP_TYPE_MAPPING:
                new_type, cat_name = OP_TYPE_MAPPING[op_type]
            # Règle 3 : provider
            elif provider_id and provider_id in provider_map:
                provider_title = provider_map[provider_id]
                for key, (t, cat) in PROVIDER_MAPPING.items():
                    if key in provider_title:
                        new_type, cat_name = t, cat
                        break

        # Fallback
        if new_type is None:
            new_type = 'EXPENSE'
            cat_name = DEFAULT_CAT

        category_id = cat_ids.get(cat_name, cat_ids[DEFAULT_CAT])
        updates.append((tx_id, new_type, category_id))

    print(f" {len(updates)} transactions à mettre à jour")

    # 6. Mise à jour en base
    execute_values(cursor, """
        UPDATE transactions
        SET type = data.type::text,
            category_id = data.category_id::uuid
        FROM (VALUES %s) AS data(id, type, category_id)
        WHERE transactions.id = data.id::uuid
    """, updates, page_size=1000)
    conn.commit()
    print(" Mise à jour terminée")

    # 7. Récapitulatif
    cursor.execute("""
        SELECT t.type, c.name, COUNT(*)
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        GROUP BY t.type, c.name
        ORDER BY t.type, COUNT(*) DESC
    """)
    print("\n RÉPARTITION APRÈS CORRECTION :")
    for type_, cat, cnt in cursor.fetchall():
        print(f"   {type_:6} | {cat:<20} : {cnt:5} transactions")

    cursor.close()
    conn.close()
    print("\n CORRECTION TERMINÉE ")

if __name__ == "__main__":
    main()