import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

def main():
    print("=" * 60)
    print("CORRECTION DES NUMÉROS DE TÉLÉPHONE BIZARRES")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Trouver tous les utilisateurs avec un numéro contenant des lettres (non numérique après +216)
    cursor.execute("""
        SELECT id, phone_number 
        FROM users 
        WHERE phone_number LIKE '%[a-z]%' 
           OR phone_number !~ '^\\+216[0-9]{8}$'
        AND role = 'USER'
    """)
    users = cursor.fetchall()
    print(f"{len(users)} utilisateurs avec des numéros invalides")

    updates = []
    for i, (user_id, old_phone) in enumerate(users, start=1):
        # Générer un numéro propre : +21690000001, +21690000002, etc.
        new_phone = f"+216900{10000 + i:05d}"  # ex: +21690010001
        updates.append((new_phone, user_id))
        print(f"  {old_phone} → {new_phone}")

    if updates:
        execute_values(cursor, """
            UPDATE users 
            SET phone_number = data.phone 
            FROM (VALUES %s) AS data(phone, id)
            WHERE users.id = data.id::uuid
        """, updates, page_size=100)
        conn.commit()
        print(f"\n {len(updates)} numéros corrigés")

    cursor.close()
    conn.close()
    print("\n TERMINÉ !")

if __name__ == "__main__":
    main()