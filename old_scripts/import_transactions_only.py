import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import uuid

# =============================================
# CHEMINS DES CSV
# =============================================
TRANSACTIONS_CSV = "output/transactions_clients.csv"

# =============================================
# CONNEXION À LA BASE
# =============================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

def main():
    print("=" * 60)
    print("IMPORT DES TRANSACTIONS UNIQUEMENT")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Récupérer l'ID de la catégorie 'Autre'
    cursor.execute("SELECT id FROM categories WHERE name = 'Autre' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print(" Catégorie 'Autre' introuvable. Création manuelle...")
        autre_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO categories (id, name, icon, color, is_system)
            VALUES (%s, 'Autre', 'category', '#64748B', true)
        """, (autre_id,))
        conn.commit()
    else:
        autre_id = row[0]

    print(f"Catégorie 'Autre' : {autre_id}")

    # Importer les transactions
    print("--- Import des transactions ---")
    df = pd.read_csv(TRANSACTIONS_CSV, sep=';', decimal=',', encoding='utf-8-sig')
    
    # Vérifier les colonnes nécessaires
    if 'client_id' not in df.columns:
        print(" Colonne 'client_id' manquante dans le CSV")
        return
    if 'amount' not in df.columns:
        print(" Colonne 'amount' manquante")
        return
    if 'transaction_date' not in df.columns:
        print(" Colonne 'transaction_date' manquante")
        return

    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df = df.dropna(subset=['client_id', 'amount', 'transaction_date'])
    df = df[df['amount'] > 0]

    if 'description' not in df.columns:
        df['description'] = df.get('reference', 'Transaction historique').fillna('')
    else:
        df['description'] = df['description'].fillna('Transaction historique')

    values = []
    for _, row in df.iterrows():
        values.append((
            str(uuid.uuid4()),
            row['client_id'],
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

    execute_values(cursor, """
        INSERT INTO transactions (id, user_id, amount, description, type, transaction_date,
                                 category_id, ai_predicted_category, ai_confidence,
                                 is_anomaly, is_recurring, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, values, page_size=500)
    
    conn.commit()
    print(f"  {len(values)} transactions importées")

    cursor.close()
    conn.close()
    print("\n IMPORT TERMINÉ !")

if __name__ == "__main__":
    main()