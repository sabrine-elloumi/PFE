import pandas as pd
from datetime import datetime

def sauvegarder_csv(df, chemin, nom_fichier):
    """Sauvegarde un DataFrame en CSV"""
    chemin_complet = f"{chemin}/{nom_fichier}"
    df.to_csv(chemin_complet, index=False, encoding='utf-8')
    print(f"   💾 Sauvegarde: {chemin_complet}")
    return chemin_complet

def sauvegarder_resume(stats, df_trans_clients, df_stats_clients, 
                       profil_counts, df_stats_agents, df_trans_agents, chemin):
    """Cree un fichier resume des resultats avec distinction clients/agents"""
    
    with open(f"{chemin}/resume_etl.txt", 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RESUME ETL - SMART PERSONAL FINANCE WALLET\n")
        f.write("="*80 + "\n\n")
        f.write(f"Date de l'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        # Partie 1: Statistiques globales
        f.write("1. STATISTIQUES GLOBALES\n")
        f.write("-" * 50 + "\n")
        f.write(f"   Transactions brutes: {stats['transactions_brutes']:,}\n")
        f.write(f"   Transactions apres nettoyage: {stats['transactions_nettoyees']:,}\n")
        f.write(f"   Taux de conservation: {stats['taux_conservation']:.1f}%\n")
        f.write(f"   Montant total: {stats['montant_total']:,.2f} TND\n")
        f.write(f"   Montant moyen par transaction: {stats['montant_moyen']:,.2f} TND\n\n")
        
        if stats['date_debut'] and stats['date_fin']:
            f.write(f"   Periode analysee:\n")
            f.write(f"      Du: {stats['date_debut']}\n")
            f.write(f"      Au: {stats['date_fin']}\n")
            f.write(f"      Duree: {stats['duree_jours']} jours\n\n")
        
        # Partie 2: Analyse Clients
        f.write("2. ANALYSE CLIENTS (Clients finaux du wallet)\n")
        f.write("-" * 50 + "\n")
        f.write(f"   Nombre de clients actifs: {len(df_stats_clients):,}\n")
        f.write(f"   Nombre total de transactions clients: {len(df_trans_clients):,}\n")
        if len(df_trans_clients) > 0 and 'amount' in df_trans_clients.columns:
            f.write(f"   Montant total traite par les clients: {df_trans_clients['amount'].sum():,.2f} TND\n")
            f.write(f"   Montant moyen par client: {df_stats_clients['montant_total'].mean():,.2f} TND\n\n")
        
        if len(profil_counts) > 0:
            f.write("   Classification des clients (6 profils):\n")
            f.write("   " + "-" * 40 + "\n")
            for profil, count in profil_counts.items():
                pourcentage = (count / len(df_stats_clients)) * 100
                if "VIP" in profil:
                    prefix = "👑"
                elif "Premium" in profil:
                    prefix = "⭐"
                elif "Gros" in profil:
                    prefix = "💰"
                elif "Micro" in profil:
                    prefix = "🔄"
                else:
                    prefix = "📊"
                f.write(f"      {prefix} {profil}: {count} clients ({pourcentage:.1f}%)\n")
            
            f.write("\n   Statistiques par profil:\n")
            for profil in profil_counts.index:
                subset = df_stats_clients[df_stats_clients['profil'] == profil]
                f.write(f"\n      {profil}:\n")
                f.write(f"         - Nombre de clients: {len(subset)}\n")
                f.write(f"         - Montant total moyen: {subset['montant_total'].mean():,.2f} TND\n")
                f.write(f"         - Transactions moyennes: {subset['nb_transactions'].mean():.1f}\n")
                f.write(f"         - Montant moyen par transaction: {subset['montant_moyen'].mean():,.2f} TND\n")
        
        f.write("\n   Top 5 clients par montant:\n")
        if len(df_stats_clients) > 0:
            top5 = df_stats_clients.nlargest(5, 'montant_total')
            for i, (_, row) in enumerate(top5.iterrows(), 1):
                f.write(f"      {i}. Client {row['client_id'][:12]}...: {row['montant_total']:,.2f} TND ({row['nb_transactions']} transactions)\n")
        
        # Partie 3: Analyse Agents
        if len(df_stats_agents) > 0:
            f.write("\n\n3. ANALYSE AGENTS (Points de vente / Commercants)\n")
            f.write("-" * 50 + "\n")
            f.write(f"   Nombre d'agents actifs: {len(df_stats_agents):,}\n")
            f.write(f"   Nombre total de transactions traitees: {len(df_trans_agents):,}\n")
            if 'amount' in df_trans_agents.columns:
                f.write(f"   Montant total traite: {df_trans_agents['amount'].sum():,.2f} TND\n")
            if 'nb_clients_servis' in df_stats_agents.columns:
                f.write(f"   Moyenne clients servis par agent: {df_stats_agents['nb_clients_servis'].mean():.1f}\n\n")
            
            if 'profil_agent' in df_stats_agents.columns:
                f.write("   Classification des agents:\n")
                agent_profil_counts = df_stats_agents['profil_agent'].value_counts()
                for profil, count in agent_profil_counts.items():
                    pourcentage = (count / len(df_stats_agents)) * 100
                    if "Premium" in profil:
                        prefix = "🏆"
                    elif "Actif" in profil:
                        prefix = "⚡"
                    else:
                        prefix = "📌"
                    f.write(f"      {prefix} {profil}: {count} agents ({pourcentage:.1f}%)\n")
            
            f.write("\n   Top 5 agents par montant traite:\n")
            top5_agents = df_stats_agents.nlargest(5, 'montant_total')
            for i, (_, row) in enumerate(top5_agents.iterrows(), 1):
                f.write(f"      {i}. Agent {row['agent_id'][:12]}...: {row['montant_total']:,.2f} TND ({row['nb_transactions']} transactions")
                if 'nb_clients_servis' in row:
                    f.write(f", {row['nb_clients_servis']} clients")
                f.write(")\n")
        
        f.write("\n\n" + "="*80 + "\n")
        f.write("FIN DU RESUME\n")
    
    print(f"   ✅ Resume sauvegarde: {chemin}/resume_etl.txt")