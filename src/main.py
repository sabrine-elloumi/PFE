import os
import sys

from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extract.extract import (charger_fichier_sql, extraire_clients, 
                                 extraire_providers, extraire_transactions,
                                 extraire_transaction_types)
from src.transform.clean import (nettoyer_transactions, 
                                 nettoyer_clients,
                                 nettoyer_providers,
                                 nettoyer_transaction_types,
                                 fusionner_avec_referentiels,
                                 garder_transactions_clients,
                                 garder_transactions_providers)
from src.transform.classify import (calculer_statistiques_clients, 
                                   classifier_clients,
                                   generer_recommandations,
                                   calculer_statistiques_providers,
                                   classifier_providers)
from src.load.load import sauvegarder_csv, sauvegarder_resume
from src.visualization.visualize import creer_graphiques, creer_graphiques_profils_avances

def main():
    print("="*70)
    print("ETL - SMART PERSONAL FINANCE WALLET")
    print("="*70)
    print()
    
    chemin_data = "data"
    chemin_output = "output"
    
    os.makedirs(chemin_output, exist_ok=True)
    
    print("1. EXTRACTION DES DONNEES")
    print("-" * 50)
    
    lignes = charger_fichier_sql(f"{chemin_data}/izitransactionmanager.sql")
    
    df_clients = extraire_clients(lignes)
    df_providers = extraire_providers(lignes)
    df_trans_brut = extraire_transactions(lignes)
    df_trans_types = extraire_transaction_types(lignes)
    
    print(f"   Clients bruts: {len(df_clients)}")
    print(f"   Fournisseurs bruts: {len(df_providers)}")
    print(f"   Transactions brutes: {len(df_trans_brut)}")
    print(f"   Types de transactions bruts: {len(df_trans_types)}")
    print()
    
    print("2. NETTOYAGE DES DONNEES")
    print("-" * 50)
    
    df_clients = nettoyer_clients(df_clients)
    df_providers = nettoyer_providers(df_providers)
    df_trans_types = nettoyer_transaction_types(df_trans_types)
    df_trans = nettoyer_transactions(df_trans_brut)
    
    print(f"   Clients apres nettoyage: {len(df_clients)}")
    print(f"   Fournisseurs apres nettoyage: {len(df_providers)}")
    print(f"   Types de transactions apres nettoyage: {len(df_trans_types)}")
    print(f"   Transactions apres nettoyage: {len(df_trans)}")
    if len(df_trans_brut) > 0:
        print(f"   Taux de conservation transactions: {(len(df_trans)/len(df_trans_brut)*100):.1f}%")
    print()
    
    print("3. FUSION AVEC REFERENTIELS")
    print("-" * 50)
    
    df_trans = fusionner_avec_referentiels(df_trans, df_clients, df_providers)
    print()
    
    print("4. FILTRAGE CLIENTS")
    print("-" * 50)
    
    df_trans_clients = garder_transactions_clients(df_trans)
    df_trans_providers = garder_transactions_providers(df_trans)
    
    print(f"   Transactions CLIENTS: {len(df_trans_clients)}")
    print(f"   Transactions FOURNISSEURS: {len(df_trans_providers)}")
    
    if len(df_trans_clients) > 0 and 'amount' in df_trans_clients.columns:
        print(f"   Montant total clients: {df_trans_clients['amount'].sum():,.2f} TND")
    print()
    
    print("5. CLASSIFICATION CLIENTS")
    print("-" * 50)
    
    if len(df_trans_clients) > 0:
        stats_clients = calculer_statistiques_clients(df_trans_clients)
        stats_clients = classifier_clients(stats_clients)
        
        if len(stats_clients) > 0:
            profil_counts = stats_clients['profil'].value_counts()
            print(f"\n   REPARTITION DES PROFILS CLIENTS:")
            for profil, count in profil_counts.items():
                print(f"      {profil}: {count} clients ({(count/len(stats_clients)*100):.1f}%)")
            
            recommendations = generer_recommandations(stats_clients, df_trans_clients, df_trans_types)
            if len(recommendations) > 0:
                sauvegarder_csv(recommendations, chemin_output, "recommandations_clients.csv")
                print(f"\n   {len(recommendations)} recommandations generees")
    else:
        stats_clients = pd.DataFrame()
        profil_counts = pd.Series()
        print("   Aucune transaction client")
    
    print()
    
    print("6. ANALYSE FOURNISSEURS")
    print("-" * 50)
    
    if len(df_trans_clients) > 0 and len(df_providers) > 0:
        stats_providers = calculer_statistiques_providers(df_trans_clients, df_providers)
        if len(stats_providers) > 0:
            stats_providers = classifier_providers(stats_providers)
            
            print(f"\n   TOP 5 FOURNISSEURS PAR MONTANT:")
            top5 = stats_providers.nlargest(5, 'montant_total')
            for _, row in top5.iterrows():
                name = row.get(row.index[0] if len(row) > 0 else 'provider_id', 'Inconnu')
                if isinstance(name, (int, float)):
                    name = f"Provider_{row['provider_id'][:8]}"
                print(f"      {str(name)[:20]}: {row['montant_total']:,.0f} TND ({row['nb_transactions']} transactions)")
            
            sauvegarder_csv(stats_providers, chemin_output, "statistiques_providers.csv")
    else:
        print("   Donnees insuffisantes pour analyse providers")
    
    print()
    
    print("7. SAUVEGARDE DES FICHIERS")
    print("-" * 50)
    
    if len(df_trans_clients) > 0:
        sauvegarder_csv(df_trans_clients, chemin_output, "transactions_clients.csv")
        sauvegarder_csv(stats_clients, chemin_output, "statistiques_clients.csv")
    
    if len(df_clients) > 0:
        sauvegarder_csv(df_clients, chemin_output, "clients_nettoyes.csv")
    
    if len(df_providers) > 0:
        sauvegarder_csv(df_providers, chemin_output, "providers_nettoyes.csv")
    
    if len(df_trans_types) > 0:
        sauvegarder_csv(df_trans_types, chemin_output, "transaction_types_nettoyes.csv")
    
    print()
    
    print("8. VISUALISATION")
    print("-" * 50)
    
    stats_globales = {
        'transactions_brutes': len(df_trans_brut),
        'transactions_nettoyees': len(df_trans),
        'taux_conservation': (len(df_trans)/len(df_trans_brut)*100) if len(df_trans_brut) > 0 else 0,
        'montant_total': df_trans['amount'].sum() if len(df_trans) > 0 and 'amount' in df_trans.columns else 0,
        'montant_moyen': df_trans['amount'].mean() if len(df_trans) > 0 and 'amount' in df_trans.columns else 0,
        'clients_avant': len(df_clients) if 'df_clients' in locals() else 0,
        'clients_apres': len(df_clients) if 'df_clients' in locals() else 0,
        'date_debut': df_trans['transaction_date'].min() if len(df_trans) > 0 and 'transaction_date' in df_trans.columns else None,
        'date_fin': df_trans['transaction_date'].max() if len(df_trans) > 0 and 'transaction_date' in df_trans.columns else None,
        'duree_jours': (df_trans['transaction_date'].max() - df_trans['transaction_date'].min()).days if len(df_trans) > 0 and 'transaction_date' in df_trans.columns else 0
    }
    
    sauvegarder_resume(stats_globales, df_trans_clients, stats_clients, 
                       profil_counts, stats_providers, df_trans_providers, chemin_output)
    
    if len(df_trans_clients) > 0 and len(stats_clients) > 0:
        try:
            creer_graphiques(df_trans_clients, stats_clients, profil_counts, chemin_output)
            if 'recommendations' in locals() and len(recommendations) > 0:
                creer_graphiques_profils_avances(stats_clients, recommendations, chemin_output)
        except Exception as e:
            print(f"   Erreur graphiques: {e}")
    
    print()
    
    print("="*70)
    print("ETL TERMINE AVEC SUCCES")
    print("="*70)
    print(f"\nResultats dans le dossier: {chemin_output}/")

if __name__ == "__main__":
    main()