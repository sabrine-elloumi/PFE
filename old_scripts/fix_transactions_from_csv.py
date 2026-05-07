import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid

# === CONFIGURATION ===
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

CSV_PATH = "output/transactions_clients.csv"

# === MAPPINGS (à ajuster selon tes observations) ===
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

PROVIDER_MAPPING = {
    'SONEDE':  ('EXPENSE', 'Eau'),
    'STEG':    ('EXPENSE', 'Électricité'),
    'TOPNET':  ('EXPENSE', 'Internet'),
    'BEE':     ('EXPENSE', 'Internet'),
    'OOREDOO': ('EXPENSE', 'Téléphonie'),
    'ORANGE':  ('EXPENSE', 'Téléphonie'),
    'TT':      ('EXPENSE', 'Téléphonie'),
    'CNTE':    ('EXPENSE', 'Éducation'),
}

DEFAULT_CAT = 'Autre'

# Liste des catégories système à créer si absentes
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
    """Retourne l'ID d'une catégorie système ; la crée si inexistante."""
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
    print("CORRECTION DES TRANSACTIONS DEPUIS LE CSV (avec mapping)")
    print("=" * 70)

    # 1. Lecture du CSV
    print(" Lecture de", CSV_PATH)
    df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
    required = ['id', 'client_id', 'amount', 'transaction_date']
    for col in required:
        if col not in df.columns:
            print(f" Colonne '{col}' manquante dans le CSV")
            return
    print(f"   {len(df)} transactions chargées")

    # 2. Connexion à PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 3. Création des catégories système si besoin
    print(" Vérification/création des catégories...")
    cat_ids = {}
    for name, icon, color in SYSTEM_CATEGORIES:
        cat_ids[name] = get_or_create_category(cursor, name, icon, color)
    cat_ids[DEFAULT_CAT] = get_or_create_category(cursor, DEFAULT_CAT, 'category', '#64748B')
    conn.commit()
    print(f"   {len(cat_ids)} catégories disponibles")

    # 4. Charger le mapping provider_title -> provider_id
    provider_map = {}
    try:
        df_prov = pd.read_csv("output/providers_nettoyes.csv", sep=';', encoding='utf-8-sig')
        if 'id' in df_prov.columns and 'title' in df_prov.columns:
            provider_map = dict(zip(df_prov['id'].astype(str), df_prov['title'].astype(str)))
        print(f"   Mapping fournisseurs chargé ({len(provider_map)} entrées)")
    except Exception as e:
        print("   Aucun fichier providers_nettoyes.csv trouvé, mapping ignoré")

    # 5. Calcul des mises à jour
    updates = []  # (id, new_type, category_id)
    for _, row in df.iterrows():
        tx_id = row['id']
        op_type = row.get('operation_type')
        provider_id = str(row.get('provider_id')) if pd.notna(row.get('provider_id')) else None
        receiver_id = row.get('receiver_id') if pd.notna(row.get('receiver_id')) else None

        new_type = None
        cat_name = None

        # Règle 1 : transfert reçu (receiver_id non null) → INCOME
        if receiver_id is not None:
            new_type = 'INCOME'
            cat_name = 'Transfert'
        else:
            # Règle 2 : operation_type
            if op_type is not None and op_type in OP_TYPE_MAPPING:
                new_type, cat_name = OP_TYPE_MAPPING[op_type]
            # Règle 3 : provider
            elif provider_id and provider_id in provider_map:
                title = provider_map[provider_id]
                for key, (t, cat) in PROVIDER_MAPPING.items():
                    if key in title:
                        new_type, cat_name = t, cat
                        break

        # Fallback
        if new_type is None:
            new_type = 'EXPENSE'
            cat_name = DEFAULT_CAT

        category_id = cat_ids.get(cat_name, cat_ids[DEFAULT_CAT])
        updates.append((tx_id, new_type, category_id))

    print(f"🔧 {len(updates)} transactions à mettre à jour")

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

    # 6. Récapitulatif
    cursor.execute("""
        SELECT type, COUNT(*) FROM transactions GROUP BY type
    """)
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