import pandas as pd

def calculer_statistiques_clients(df_transactions_clients):
    """Calcule les statistiques pour chaque client"""
    if len(df_transactions_clients) == 0:
        return pd.DataFrame()
    
    if 'client_id' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    if 'amount' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    stats = df_transactions_clients.groupby('client_id').agg({
        'amount': ['count', 'sum', 'mean', 'std', 'min', 'max'],
        'transaction_date': ['min', 'max']
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen', 
                     'ecart_type', 'montant_min', 'montant_max',
                     'premiere_transaction', 'derniere_transaction']
    
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    # Calcul de la durée d'activité (éviter division par zéro)
    stats['duree_activite_jours'] = (stats['derniere_transaction'] - stats['premiere_transaction']).dt.days
    stats['duree_activite_jours'] = stats['duree_activite_jours'].clip(lower=1)
    
    stats['frequence_mensuelle'] = stats['nb_transactions'] / (stats['duree_activite_jours'] / 30)
    stats['coefficient_variation'] = stats['ecart_type'] / stats['montant_moyen'].clip(lower=0.01)
    stats['coefficient_variation'] = stats['coefficient_variation'].fillna(0)
    
    today = df_transactions_clients['transaction_date'].max()
    stats['recence_jours'] = (today - stats['derniere_transaction']).dt.days
    
    stats = stats.sort_values('montant_total', ascending=False).reset_index(drop=True)
    
    return stats

def classifier_clients(stats_clients):
    """
    Classification des clients en 4 profils distincts
    Profils: Premium, Gros dépensier actif, Client régulier, Client occasionnel
    """
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    # Calcul des seuils
    percentiles = {
        'freq_high': df['nb_transactions'].quantile(0.75),
        'freq_medium': df['nb_transactions'].quantile(0.50),
        'amount_high': df['montant_moyen'].quantile(0.75),
        'amount_medium': df['montant_moyen'].quantile(0.50),
        'total_high': df['montant_total'].quantile(0.80),
    }
    
    print(f"\n SEUILS DE CLASSIFICATION (4 profils):")
    print(f"   Transactions: Haut≥{percentiles['freq_high']:.0f} | Médian≥{percentiles['freq_medium']:.0f}")
    print(f"   Montant moyen: Haut≥{percentiles['amount_high']:.0f} | Médian≥{percentiles['amount_medium']:.0f}")
    print(f"   Montant total (Premium): Top 20% ≥{percentiles['total_high']:,.0f} TND")
    
    def classifier(row):
        # Profil 1: Premium
        if row['montant_total'] >= percentiles['total_high']:
            return "Premium"
        
        # Catégories de fréquence
        if row['nb_transactions'] >= percentiles['freq_high']:
            freq_cat = "tres_actif"
        elif row['nb_transactions'] >= percentiles['freq_medium']:
            freq_cat = "actif"
        else:
            freq_cat = "occasionnel"
        
        # Catégories de montant
        if row['montant_moyen'] >= percentiles['amount_high']:
            amount_cat = "gros"
        elif row['montant_moyen'] >= percentiles['amount_medium']:
            amount_cat = "modere"
        else:
            amount_cat = "petit"
        
        # Profil 2: Gros dépensier actif
        if amount_cat == "gros" and freq_cat in ["tres_actif", "actif"]:
            return "Gros dépensier actif"
        
        # Profil 3: Client régulier
        if freq_cat in ["tres_actif", "actif"]:
            return "Client régulier"
        
        # Profil 4: Client occasionnel
        return "Client occasionnel"
    
    df['profil'] = df.apply(classifier, axis=1)
    
    # Affichage des résultats
    profil_counts = df['profil'].value_counts()
    print(f"\n RÉPARTITION DES 4 PROFILS:")
    for profil, count in profil_counts.items():
        pourcentage = count / len(df) * 100
        barre = "█" * int(pourcentage / 2)
        print(f"   {profil:<20} : {count:>4} clients ({pourcentage:>5.1f}%) {barre}")
    
    return df

def generer_recommandations(stats_clients, df_transactions, df_trans_types=None):
    """Génère des recommandations personnalisées pour les 4 profils"""
    if len(stats_clients) == 0:
        return pd.DataFrame()
    
    recommendations = []
    
    rec_mapping = {
        "Premium": {
            'rec1': "Programme fidélité Premium - Cashback majoré à 5%",
            'rec2': "Accès exclusif aux offres partenaires premium",
            'rec3': "Conseiller financier dédié",
            'alert': "Objectif : Maintenez votre statut Premium avec >5000 TND/mois",
            'type': 'premium'
        },
        "Gros dépensier actif": {
            'rec1': "Cashback 3% sur vos catégories favorites",
            'rec2': "Offres personnalisées basées sur vos achats",
            'rec3': "Rapport mensuel détaillé",
            'alert': "Objectif Premium : Atteignez 5000 TND/mois",
            'type': 'premium'
        },
        "Client régulier": {
            'rec1': "Programme de parrainage - Gagnez 50 TND par ami",
            'rec2': "Catégories suggérées pour optimiser votre cashback",
            'rec3': "Budget personnalisé basé sur vos habitudes",
            'alert': "Effectuez 3 transactions/semaine pour +50% de cashback",
            'type': 'fidelisation'
        },
        "Client occasionnel": {
            'rec1': "50 TND offerts pour votre prochaine transaction",
            'rec2': "Découvrez les fonctionnalités du wallet",
            'rec3': "Cashback 5% pendant 3 mois",
            'alert': "Activez votre wallet dès aujourd'hui",
            'type': 'acquisition'
        }
    }
    
    for _, client in stats_clients.iterrows():
        profil = client['profil']
        rec_template = rec_mapping.get(profil, rec_mapping["Client occasionnel"])
        
        rec = {
            'client_id': client['client_id'],
            'profil': profil,
            'montant_total': client['montant_total'],
            'nb_transactions': client['nb_transactions'],
            'montant_moyen': client['montant_moyen'],
            'recommendation_1': rec_template['rec1'],
            'recommendation_2': rec_template['rec2'],
            'recommendation_3': rec_template['rec3'],
            'recommendation_alert': rec_template['alert'],
            'recommandation_type': rec_template['type']
        }
        
        recommendations.append(rec)
    
    print(f"\n {len(recommendations)} recommandations générées")
    return pd.DataFrame(recommendations)

def calculer_statistiques_providers(df_transactions, df_providers):
    """Calcule les statistiques pour chaque fournisseur"""
    if len(df_transactions) == 0 or len(df_providers) == 0:
        return pd.DataFrame()
    
    if 'provider_id' not in df_transactions.columns:
        return pd.DataFrame()
    
    if 'amount' not in df_transactions.columns:
        return pd.DataFrame()
    
    stats = df_transactions.groupby('provider_id').agg({
        'amount': ['count', 'sum', 'mean'],
        'client_id': 'nunique'
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen', 'nb_clients']
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    if len(df_providers) > 0:
        provider_col = df_providers.columns[0]
        stats = stats.merge(df_providers[[provider_col]], left_on='provider_id', right_on=provider_col, how='left')
    
    return stats

def classifier_providers(stats_providers):
    """Classification des fournisseurs en catégories"""
    if len(stats_providers) == 0:
        return stats_providers
    
    df = stats_providers.copy()
    
    if len(df) > 0:
        seuil_transactions = df['nb_transactions'].quantile(0.75)
        seuil_montant = df['montant_total'].quantile(0.75)
        
        def classifier(row):
            if row['nb_transactions'] >= seuil_transactions and row['montant_total'] >= seuil_montant:
                return "Fournisseur Premium"
            elif row['nb_transactions'] >= seuil_transactions:
                return "Fournisseur Actif"
            elif row['montant_total'] >= seuil_montant:
                return "Fournisseur Occasionnel (Gros montants)"
            else:
                return "Fournisseur Standard"
        
        df['profil_provider'] = df.apply(classifier, axis=1)
        
        print(f"\n RÉPARTITION DES FOURNISSEURS:")
        profil_counts = df['profil_provider'].value_counts()
        for profil, count in profil_counts.items():
            pourcentage = count / len(df) * 100
            print(f"   {profil:<35} : {count:>3} ({pourcentage:.1f}%)")
    
    return df