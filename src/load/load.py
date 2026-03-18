import pandas as pd
from datetime import datetime

def sauvegarder_csv(df, chemin, nom_fichier):
    """Sauvegarde un DataFrame en CSV"""
    chemin_complet = f"{chemin}/{nom_fichier}"
    df.to_csv(chemin_complet, index=False, encoding='utf-8')
    return chemin_complet

def sauvegarder_resume(stats, df_trans, df_stats, profil_counts, chemin):
    """Cree un fichier resume des resultats"""
    with open(f"{chemin}/resume_etl.txt", 'w', encoding='utf-8') as f:
        f.write("RESUME ETL - SMART PERSONAL FINANCE WALLET\n\n")
        f.write(f"Date de l'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("STATISTIQUES GLOBALES:\n")
        f.write(f"  Nombre de transactions: {stats['transactions_brutes']:,}\n")
        f.write(f"  Transactions apres nettoyage: {stats['transactions_nettoyees']:,}\n")
        f.write(f"  Montant total: {stats['montant_total']:,.2f}\n")
        f.write(f"  Montant moyen: {stats['montant_moyen']:,.2f}\n\n")
        
        f.write("PERIODE ANALYSEE:\n")
        f.write(f"  Du: {stats['date_debut']}\n")
        f.write(f"  Au: {stats['date_fin']}\n\n")
        
        f.write("CLASSIFICATION DES CLIENTS:\n")
        for profil, count in profil_counts.items():
            pourcentage = (count / len(df_stats)) * 100
            f.write(f"  {profil}: {count} clients ({pourcentage:.1f}%)\n")