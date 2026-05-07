import pandas as pd
from datetime import datetime

def sauvegarder_csv(df, chemin, nom_fichier):
    """Sauvegarde un DataFrame en CSV (propre pour Power BI)"""
    if len(df) == 0:
        print(f"Aucune donnée à sauvegarder pour {nom_fichier}")
        return None
    
    chemin_complet = f"{chemin}/{nom_fichier}"
    
    # Nettoyer les valeurs problématiques
    df = df.copy()
    
    # Remplacer les NaN par des valeurs appropriées
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('')
        elif df[col].dtype in ['float64', 'int64']:
            df[col] = df[col].fillna(0)
    
    # Pour Power BI : séparateur point-virgule, encodage UTF-8 avec BOM
    df.to_csv(
        chemin_complet, 
        index=False, 
        encoding='utf-8-sig',  # UTF-8 avec BOM (Power BI l'aime bien)
        sep=';',                # séparateur point-virgule
        decimal=','             # virgule pour les décimales
    )
    print(f"Sauvegarde: {chemin_complet} ({len(df)} lignes)")
    return chemin_complet

def sauvegarder_resume(stats, df_trans_clients, df_stats_clients, 
                       profil_counts, df_stats_providers, df_trans_providers, chemin):
    """Sauvegarde un résumé texte de l'ETL"""
    with open(f"{chemin}/resume_etl.txt", 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("RESUME ETL - SMART PERSONAL FINANCE WALLET\n")
        f.write("="*70 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("1. STATISTIQUES GLOBALES\n")
        f.write("-" * 50 + "\n")
        f.write(f"   Transactions brutes: {stats['transactions_brutes']:,}\n")
        f.write(f"   Transactions apres nettoyage: {stats['transactions_nettoyees']:,}\n")
        f.write(f"   Taux de conservation: {stats['taux_conservation']:.1f}%\n")
        f.write(f"   Montant total: {stats['montant_total']:,.2f} TND\n")
        f.write(f"   Montant moyen: {stats['montant_moyen']:,.2f} TND\n\n")
        
        if stats['date_debut'] and stats['date_fin']:
            f.write(f"   Periode: {stats['date_debut']} - {stats['date_fin']}\n")
            f.write(f"   Duree: {stats['duree_jours']} jours\n\n")
        
        f.write("2. ANALYSE CLIENTS\n")
        f.write("-" * 50 + "\n")
        f.write(f"   Clients actifs: {len(df_stats_clients):,}\n")
        f.write(f"   Transactions clients: {len(df_trans_clients):,}\n")
        if len(df_trans_clients) > 0 and 'amount' in df_trans_clients.columns:
            f.write(f"   Montant total: {df_trans_clients['amount'].sum():,.2f} TND\n\n")
        
        if len(profil_counts) > 0:
            f.write("   Classification clients:\n")
            for profil, count in profil_counts.items():
                pourcentage = (count / len(df_stats_clients)) * 100
                f.write(f"      {profil}: {count} clients ({pourcentage:.1f}%)\n")
        
        if len(df_stats_providers) > 0:
            f.write("\n3. ANALYSE FOURNISSEURS\n")
            f.write("-" * 50 + "\n")
            f.write(f"   Fournisseurs actifs: {len(df_stats_providers):,}\n")
            if len(df_trans_providers) > 0:
                f.write(f"   Transactions: {len(df_trans_providers):,}\n")
            if 'montant_total' in df_stats_providers.columns:
                f.write(f"   Montant total: {df_stats_providers['montant_total'].sum():,.2f} TND\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("FIN DU RESUME\n")
    
    print(f"Resume sauvegarde: {chemin}/resume_etl.txt")