import bcrypt
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "smart_finance_wallet",
    "user": "wallet_user",
    "password": "wallet_password"
}

def main():
    # 1. Générer le hash du mot de passe Admin123
    password = b"Admin123"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    print(f"Hash généré : {hashed}")

    # 2. Connexion à PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 3. Supprimer l'ancien admin s'il existe
    cursor.execute("DELETE FROM users WHERE phone_number = '+21600000000'")

    # 4. Créer le nouvel admin
    cursor.execute("""
        INSERT INTO users (id, phone_number, password, first_name, last_name, email, role, active, preferred_currency, created_at, profile_type)
        VALUES (gen_random_uuid(), %s, %s, 'Admin', 'System', 'admin@excellia.tn', 'ADMIN', true, 'TND', NOW(), NULL)
    """, ('+21600000000', hashed))

    conn.commit()
    print("    Admin créé avec succès")
    print("   Téléphone : +21600000000")
    print("   Mot de passe : Admin123")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()