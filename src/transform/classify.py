import pandas as pd

def calculer_statistiques_clients(df_avec_clients):
    """Calcule les statistiques par client"""
    stats = df_avec_clients.groupby('client_id').agg({
        'amount': ['count', 'sum', 'mean']
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen']
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    return stats

def classifier_clients(stats_clients):
    """Classifie les clients selon leur comportement"""
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    seuil_frequence = df['nb_transactions'].median()
    seuil_montant = df['montant_moyen'].median()
    
    def classifier(row):
        if row['nb_transactions'] >= seuil_frequence and row['montant_moyen'] >= seuil_montant:
            return "Gros depensier regulier"
        elif row['nb_transactions'] >= seuil_frequence and row['montant_moyen'] < seuil_montant:
            return "Petit depensier regulier"
        elif row['nb_transactions'] < seuil_frequence and row['montant_moyen'] >= seuil_montant:
            return "Gros depensier occasionnel"
        else:
            return "Petit depensier occasionnel"
    
    df['profil'] = df.apply(classifier, axis=1)
    
    return df, {'frequence': seuil_frequence, 'montant': seuil_montant}