import os
import sys

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extract.extract import charger_fichier_sql, extraire_clients, extraire_transactions
from src.transform.clean import nettoyer_transactions, fusionner_avec_clients
from src.transform.classify import calculer_statistiques_clients, classifier_clients
from src.load.load import sauvegarder_csv, sauvegarder_resume
from src.visualization.visualize import creer_graphiques

def main():
    print("ETL - SMART PERSONAL FINANCE WALLET")
    print("")
    
    # Parametres
    chemin_data = "data"
    chemin_output = "output"
    
    # Creation des dossiers si necessaire
    os.makedirs(chemin_output, exist_ok=True)
    
    # Etape 1: Extraction
    print("1. EXTRACTION")
    lignes = charger_fichier_sql(f"{chemin_data}/izitransactionmanager.sql")
    df_clients = extraire_clients(lignes)
    df_trans_brut = extraire_transactions(lignes)
    print(f"   Clients: {len(df_clients)}")
    print(f"   Transactions: {len(df_trans_brut)}")
    print("")
    
    # Etape 2: Transformation et nettoyage
    print("2. TRANSFORMATION")
    df_trans = nettoyer_transactions(df_trans_brut)
    df_avec_clients = fusionner_avec_clients(df_trans, df_clients)
    print(f"   Transactions apres nettoyage: {len(df_trans)}")
    print(f"   Montant total: {df_trans['amount'].sum():,.2f}")
    print("")
    
    # Etape 3: Classification
    print("3. CLASSIFICATION")
    stats_clients = calculer_statistiques_clients(df_avec_clients)
    stats_clients, seuils = classifier_clients(stats_clients)
    profil_counts = stats_clients['profil'].value_counts()
    for profil, count in profil_counts.items():
        print(f"   {profil}: {count}")
    print("")
    
    # Etape 4: Chargement (sauvegarde)
    print("4. CHARGEMENT")
    sauvegarder_csv(df_trans, chemin_output, "transactions_nettoyees.csv")
    sauvegarder_csv(stats_clients, chemin_output, "statistiques_clients.csv")
    print("   Fichiers CSV sauvegardes")
    print("")
    
    # Etape 5: Visualisation
    print("5. VISUALISATION")
    stats_globales = {
        'transactions_brutes': len(df_trans_brut),
        'transactions_nettoyees': len(df_trans),
        'montant_total': df_trans['amount'].sum(),
        'montant_moyen': df_trans['amount'].mean(),
        'date_debut': df_trans['transaction_date'].min(),
        'date_fin': df_trans['transaction_date'].max()
    }
    sauvegarder_resume(stats_globales, df_trans, stats_clients, profil_counts, chemin_output)
    creer_graphiques(df_trans, stats_clients, profil_counts, chemin_output)
    print("   Resume et graphiques crees")
    print("")
    
    print("ETL TERMINE AVEC SUCCES")
    print(f"Resultats dans le dossier: {chemin_output}/")

if __name__ == "__main__":
    main()