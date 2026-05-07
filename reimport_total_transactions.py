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

DEFAULT_CAT = 'Autre'

# Catégories système nécessaires
SYSTEM_CATEGORIES = [
    ('Recharge Téléphone', 'phone_android', '#F59E0B'),
    ('Paiement Factures', 'receipt', '#3B82F6'),
    ('Transfert', 'swap_horiz', '#8B5CF6'),
    ('Paiement Marchand', 'shopping_cart', '#EC4899'),
    ('Frais', 'money_off', '#EF4444'),
    ('Commission', 'percent', '#F59E0B'),
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
    print("RÉIMPORTATION COMPLÈTE DES TRANSACTIONS")
    print("=" * 70)

    df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
    print(f" {len(df)} transactions chargées")

    # Vérifier les colonnes nécessaires
    required = ['id', 'client_id', 'amount', 'transaction_date']
    for col in required:
        if col not in df.columns:
            print(f" Colonne '{col}' absente")
            return

    # Déterminer le type et la catégorie
    df['type'] = 'EXPENSE'
    df['category_name'] = DEFAULT_CAT
    for op, (typ, cat) in OP_TYPE_MAPPING.items():
        mask = df['operation_type'] == op
        df.loc[mask, 'type'] = typ
        df.loc[mask, 'category_name'] = cat

    # S'assurer que la catégorie 'Autre' existe
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cat_ids = {}
    for name, icon, color in SYSTEM_CATEGORIES:
        cat_ids[name] = get_or_create_category(cursor, name, icon, color)
    cat_ids[DEFAULT_CAT] = get_or_create_category(cursor, DEFAULT_CAT, 'category', '#64748B')
    conn.commit()

    # Ajouter la colonne category_id
    df['category_id'] = df['category_name'].map(cat_ids)

    # Supprimer toutes les transactions existantes (si tu veux remplacer)
    print("  Suppression des transactions existantes...")
    cursor.execute("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE")
    conn.commit()

    # Préparer les valeurs pour insertion
    values = []
    for _, row in df.iterrows():
        values.append((
            row['id'],
            row['client_id'],
            float(row['amount']),
            str(row.get('description', 'Transaction historique'))[:255],
            row['type'],
            row['transaction_date'],
            row['category_id'],
            None,  # ai_predicted_category
            None,  # ai_confidence
            False, # is_anomaly
            False, # is_recurring
            row['transaction_date'],  # created_at
            row['transaction_date']   # updated_at
        ))

    print(f" Insertion de {len(values)} transactions...")
    execute_values(cursor, """
        INSERT INTO transactions (id, user_id, amount, description, type, transaction_date,
                                  category_id, ai_predicted_category, ai_confidence,
                                  is_anomaly, is_recurring, created_at, updated_at)
        VALUES %s
    """, values, page_size=1000)
    conn.commit()

    # Vérification
    cursor.execute("SELECT type, COUNT(*) FROM transactions GROUP BY type")
    print("\n Types après réimport :")
    for t, cnt in cursor.fetchall():
        print(f"   {t} : {cnt}")

    cursor.execute("""
        SELECT c.name, COUNT(*)
        FROM transactions t JOIN categories c ON t.category_id = c.id
        GROUP BY c.name
        ORDER BY COUNT(*) DESC
    """)
    print("\n Catégories :")
    for cat, cnt in cursor.fetchall():
        print(f"   {cat:<25} : {cnt:5}")

    cursor.close()
    conn.close()
    print("\n RÉIMPORTATION TERMINÉE !")

if __name__ == "__main__":
    main()