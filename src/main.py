import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extract.extract import (charger_fichier_sql, extraire_clients, 
                                 extraire_agents, extraire_transactions,
                                 extraire_transaction_types)
from src.transform.clean import (nettoyer_transactions, 
                                 fusionner_avec_referentiels,
                                 garder_transactions_clients,
                                 garder_transactions_agents)
from src.transform.classify import (calculer_statistiques_clients, 
                                   classifier_clients,
                                   generer_recommandations,
                                   calculer_statistiques_agents,
                                   classifier_agents)
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
    
    # =============================================================
    # Etape 1: Extraction
    # =============================================================
    print("1. EXTRACTION DES DONNEES")
    print("-" * 50)
    
    lignes = charger_fichier_sql(f"{chemin_data}/izitransactionmanager.sql")
    
    df_clients = extraire_clients(lignes)
    df_agents = extraire_agents(lignes)
    df_trans_brut = extraire_transactions(lignes)
    df_trans_types = extraire_transaction_types(lignes)
    
    print(f"   Clients extraits: {len(df_clients)}")
    print(f"   Agents extraits: {len(df_agents)}")
    print(f"   Transactions brutes: {len(df_trans_brut)}")
    print(f"   Types de transactions: {len(df_trans_types)}")
    print()
    
    # Afficher les colonnes trouvées pour debug
    if len(df_trans_brut) > 0:
        print(f"   Colonnes transactions: {list(df_trans_brut.columns)}")
    print()
    
    # =============================================================
    # Etape 2: Nettoyage et fusion
    # =============================================================
    print("2. NETTOYAGE ET FUSION")
    print("-" * 50)
    
    df_trans = nettoyer_transactions(df_trans_brut)
    df_trans = fusionner_avec_referentiels(df_trans, df_clients, df_agents)
    
    print(f"   Transactions apres nettoyage: {len(df_trans)}")
    if len(df_trans_brut) > 0:
        print(f"   Taux de conservation: {(len(df_trans)/len(df_trans_brut)*100):.1f}%")
    print()
    
    # =============================================================
    # Etape 3: Separation Clients vs Agents
    # =============================================================
    print("3. SEPARATION CLIENTS VS AGENTS")
    print("-" * 50)
    
    df_trans_clients = garder_transactions_clients(df_trans)
    df_trans_agents = garder_transactions_agents(df_trans)
    
    print(f"   Transactions CLIENTS (clients finaux): {len(df_trans_clients)}")
    print(f"   Transactions AGENTS (points de vente): {len(df_trans_agents)}")
    
    if len(df_trans_clients) > 0 and 'amount' in df_trans_clients.columns:
        print(f"   Montant total clients: {df_trans_clients['amount'].sum():,.2f} TND")
    if len(df_trans_agents) > 0 and 'amount' in df_trans_agents.columns:
        print(f"   Montant total agents: {df_trans_agents['amount'].sum():,.2f} TND")
    print()
    
    # =============================================================
    # Etape 4: Classification Clients (6 profils)
    # =============================================================
    print("4. CLASSIFICATION CLIENTS (6 PROFILS)")
    print("-" * 50)
    
    if len(df_trans_clients) > 0:
        # Calculer les statistiques clients
        stats_clients = calculer_statistiques_clients(df_trans_clients)
        
        # Classifier en 6 profils
        stats_clients = classifier_clients(stats_clients)
        
        if len(stats_clients) > 0 and 'profil' in stats_clients.columns:
            profil_counts = stats_clients['profil'].value_counts()
            
            print(f"\n   📊 REPARTITION DES {len(profil_counts)} PROFILS CLIENTS:")
            print("   " + "-" * 40)
            for profil, count in profil_counts.items():
                pourcentage = (count / len(stats_clients)) * 100
                # Ajouter des emojis selon le profil
                if "VIP" in profil:
                    emoji = "👑"
                elif "Premium" in profil:
                    emoji = "⭐"
                elif "Gros" in profil:
                    emoji = "💰"
                elif "Micro" in profil:
                    emoji = "🔄"
                elif "occasionnel" in profil:
                    emoji = "📅"
                else:
                    emoji = "📊"
                print(f"      {emoji} {profil}: {count} clients ({pourcentage:.1f}%)")
            
            # Afficher les statistiques par profil
            print(f"\n   📈 STATISTIQUES PAR PROFIL:")
            print("   " + "-" * 40)
            for profil in profil_counts.index:
                subset = stats_clients[stats_clients['profil'] == profil]
                print(f"      {profil}:")
                print(f"         - Montant total moyen: {subset['montant_total'].mean():,.2f} TND")
                print(f"         - Transactions moyennes: {subset['nb_transactions'].mean():.1f}")
                print(f"         - Montant moyen par transaction: {subset['montant_moyen'].mean():,.2f} TND")
            
            # Générer les recommandations personnalisées
            print(f"\n   🎯 GÉNÉRATION DES RECOMMANDATIONS PERSONNALISÉES:")
            print("   " + "-" * 40)
            recommendations = generer_recommandations(stats_clients, df_trans_clients, df_trans_types)
            
            if len(recommendations) > 0:
                sauvegarder_csv(recommendations, chemin_output, "recommandations_clients.csv")
                
                # Afficher un résumé des recommandations par type
                if 'recommandation_type' in recommendations.columns:
                    type_counts = recommendations['recommandation_type'].value_counts()
                    print(f"      Types de recommandations générées:")
                    for rec_type, count in type_counts.items():
                        type_emoji = {
                            'premium': '👑',
                            'engagement': '🎯',
                            'fidelisation': '❤️',
                            'standard': '📊',
                            'education': '📚',
                            'acquisition': '🎁'
                        }.get(rec_type, '📌')
                        print(f"         {type_emoji} {rec_type.upper()}: {count} clients")
                
                print(f"\n      ✅ {len(recommendations)} recommandations personnalisées générées")
                print(f"      📁 Fichier: {chemin_output}/recommandations_clients.csv")
        else:
            profil_counts = pd.Series()
            recommendations = pd.DataFrame()
            print("   ⚠️ Classification non disponible")
    else:
        stats_clients = pd.DataFrame()
        profil_counts = pd.Series()
        recommendations = pd.DataFrame()
        print("   ❌ Aucune transaction client trouvee")
    
    print()
    
    # =============================================================
    # Etape 5: Classification Agents
    # =============================================================
    print("5. CLASSIFICATION AGENTS")
    print("-" * 50)
    
    if len(df_trans_agents) > 0:
        stats_agents = calculer_statistiques_agents(df_trans_agents)
        stats_agents = classifier_agents(stats_agents)
        
        if len(stats_agents) > 0 and 'profil_agent' in stats_agents.columns:
            agent_profil_counts = stats_agents['profil_agent'].value_counts()
            
            print(f"\n   📊 REPARTITION DES PROFILS AGENTS:")
            print("   " + "-" * 40)
            for profil, count in agent_profil_counts.items():
                pourcentage = (count / len(stats_agents)) * 100
                if "Premium" in profil:
                    emoji = "🏆"
                elif "Actif" in profil:
                    emoji = "⚡"
                else:
                    emoji = "📌"
                print(f"      {emoji} {profil}: {count} agents ({pourcentage:.1f}%)")
            
            # Sauvegarder les statistiques agents
            sauvegarder_csv(stats_agents, chemin_output, "statistiques_agents.csv")
        else:
            print("   ⚠️ Classification agents non disponible")
    else:
        stats_agents = pd.DataFrame()
        print("   ❌ Aucune transaction agent trouvee")
    
    print()
    
    # =============================================================
    # Etape 6: Sauvegarde CSV
    # =============================================================
    print("6. SAUVEGARDE CSV")
    print("-" * 50)
    
    if len(df_trans_clients) > 0:
        sauvegarder_csv(df_trans_clients, chemin_output, "transactions_clients.csv")
        sauvegarder_csv(stats_clients, chemin_output, "statistiques_clients.csv")
        print(f"   ✅ Transactions clients sauvegardées: {len(df_trans_clients)} lignes")
        print(f"   ✅ Statistiques clients sauvegardées: {len(stats_clients)} clients")
    
    if len(df_trans_agents) > 0:
        sauvegarder_csv(df_trans_agents, chemin_output, "transactions_agents.csv")
        print(f"   ✅ Transactions agents sauvegardées: {len(df_trans_agents)} lignes")
    
    if len(df_trans_types) > 0:
        sauvegarder_csv(df_trans_types, chemin_output, "transaction_types.csv")
        print(f"   ✅ Types de transactions sauvegardés: {len(df_trans_types)} types")
    
    print()
    
    # =============================================================
    # Etape 7: Resume et Visualisation
    # =============================================================
    print("7. RESUME ET VISUALISATION")
    print("-" * 50)
    
    # Statistiques globales
    if len(df_trans) > 0:
        stats_globales = {
            'transactions_brutes': len(df_trans_brut),
            'transactions_nettoyees': len(df_trans),
            'taux_conservation': (len(df_trans)/len(df_trans_brut)*100) if len(df_trans_brut) > 0 else 0,
            'montant_total': df_trans['amount'].sum() if 'amount' in df_trans.columns else 0,
            'montant_moyen': df_trans['amount'].mean() if 'amount' in df_trans.columns else 0,
            'date_debut': df_trans['transaction_date'].min() if 'transaction_date' in df_trans.columns and len(df_trans) > 0 else None,
            'date_fin': df_trans['transaction_date'].max() if 'transaction_date' in df_trans.columns and len(df_trans) > 0 else None,
            'duree_jours': (df_trans['transaction_date'].max() - df_trans['transaction_date'].min()).days if 'transaction_date' in df_trans.columns and len(df_trans) > 0 else 0
        }
    else:
        stats_globales = {
            'transactions_brutes': len(df_trans_brut),
            'transactions_nettoyees': 0,
            'taux_conservation': 0,
            'montant_total': 0,
            'montant_moyen': 0,
            'date_debut': None,
            'date_fin': None,
            'duree_jours': 0
        }
    
    # Sauvegarder le résumé
    sauvegarder_resume(stats_globales, df_trans_clients, stats_clients, 
                       profil_counts, stats_agents, df_trans_agents, chemin_output)
    
    # Créer les graphiques
    print("\n   📊 Création des graphiques...")
    try:
        creer_graphiques(df_trans_clients, stats_clients, profil_counts, chemin_output)
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la création des graphiques principaux: {e}")
    
    # Créer les graphiques avancés des recommandations
    if len(recommendations) > 0:
        try:
            creer_graphiques_profils_avances(stats_clients, recommendations, chemin_output)
        except Exception as e:
            print(f"   ⚠️ Erreur lors de la création des graphiques avancés: {e}")
    
    print()
    
    # =============================================================
    # Etape 8: Rapport final
    # =============================================================
    print("8. RAPPORT FINAL")
    print("-" * 50)
    
    print(f"\n   📁 Tous les fichiers ont été sauvegardés dans: {chemin_output}/")
    print("\n   Fichiers générés:")
    
    # Lister les fichiers générés
    fichiers = os.listdir(chemin_output)
    for f in sorted(fichiers):
        taille = os.path.getsize(f"{chemin_output}/{f}")
        if taille < 1024:
            taille_str = f"{taille} B"
        elif taille < 1024 * 1024:
            taille_str = f"{taille / 1024:.1f} KB"
        else:
            taille_str = f"{taille / (1024 * 1024):.1f} MB"
        
        if f.endswith('.png'):
            print(f"      🖼️  {f} ({taille_str})")
        elif f.endswith('.csv'):
            print(f"      📊 {f} ({taille_str})")
        elif f.endswith('.txt'):
            print(f"      📄 {f} ({taille_str})")
        else:
            print(f"      📁 {f} ({taille_str})")
    
    print()
    
    # =============================================================
    # Fin
    # =============================================================
    print("="*70)
    print("ETL TERMINE AVEC SUCCES")
    print("="*70)
    print()
    print("Résumé de l'analyse:")
    print(f"   • {len(df_trans_clients):,} transactions clients analysées")
    print(f"   • {len(stats_clients):,} clients actifs identifiés")
    print(f"   • {len(profil_counts)} profils clients distincts")
    if len(recommendations) > 0:
        print(f"   • {len(recommendations):,} recommandations personnalisées générées")
    if len(df_trans_agents) > 0:
        print(f"   • {len(stats_agents):,} agents actifs identifiés")
    print()
    
    print("="*70)


if __name__ == "__main__":
    main()

    



    