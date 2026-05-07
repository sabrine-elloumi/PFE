import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# === Configuration ===
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

CSV_PATH = "output/transactions_clients.csv"

# === Mapping : (operation_type, code_autorisation) -> (nom_categorie, type)
# Tu dois compléter ce dictionnaire selon les valeurs réelles de ton CSV
MAPPING = {
    # Recharge téléphone
    ('0001', None): ('Recharge Téléphone', 'EXPENSE'),
    ('0002', None): ('Recharge Téléphone', 'EXPENSE'),
    ('0003', None): ('Recharge Téléphone', 'EXPENSE'),
    # Cash In (dépôt) -> REVENU
    ('N1', None): ('Cash In', 'INCOME'),
    ('N3', None): ('Cash In', 'INCOME'),
    # Cash Out (retrait) -> DEPENSE
    ('UL', None): ('Cash Out', 'EXPENSE'),
    # Paiement factures
    ('PS', None): ('Paiement Factures', 'EXPENSE'),
    ('ST', None): ('Paiement Factures', 'EXPENSE'),
    ('EN', None): ('Paiement Factures', 'EXPENSE'),
    # Transfert international
    ('RA', None): ('Transfert International', 'EXPENSE'),
    ('RD', None): ('Transfert International', 'EXPENSE'),
    # Ajoute ici tous les codes que tu observes
}

def main():
    print("Lecture du CSV...")
    df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
    print(f"{len(df)} transactions chargées")

    # Connexion à PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Récupérer l'ID de chaque catégorie système
    cursor.execute("SELECT name, id FROM categories WHERE is_system = true")
    cat_map = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"Catégories disponibles : {list(cat_map.keys())}")

    # Préparer les mises à jour
    updates = []  # (transaction_id, category_id, type)
    for _, row in df.iterrows():
        op_type = str(row.get('operation_type', '')).strip()
        code_auth = str(row.get('code_autorisation', '')).strip()
        tx_id = row['id']

        # Chercher une correspondance
        matched = False
        for (op, code), (cat_name, tx_type) in MAPPING.items():
            if op and op_type != op:
                continue
            if code and code_auth != code:
                continue
            if cat_name in cat_map:
                updates.append((tx_id, cat_map[cat_name], tx_type))
                matched = True
                break

        if not matched:
            # Facultatif : mise à jour vers 'Autre' si tu veux, sinon ignore
            pass

    print(f"{len(updates)} transactions à mettre à jour")

    if updates:
        execute_values(cursor, """
            UPDATE transactions 
            SET category_id = data.category_id,
                type = data.type
            FROM (VALUES %s) AS data(id, category_id, type)
            WHERE transaction.id = data.id
        """, updates, page_size=1000)
        conn.commit()
        print("Mise à jour terminée")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()