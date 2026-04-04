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
    
    stats['duree_activite_jours'] = (stats['derniere_transaction'] - stats['premiere_transaction']).dt.days
    stats['frequence_mensuelle'] = stats['nb_transactions'] / (stats['duree_activite_jours'] / 30).clip(lower=0.1)
    stats['coefficient_variation'] = stats['ecart_type'] / stats['montant_moyen'].clip(lower=0.01)
    stats['coefficient_variation'] = stats['coefficient_variation'].fillna(0)
    
    today = df_transactions_clients['transaction_date'].max()
    stats['recence_jours'] = (today - stats['derniere_transaction']).dt.days
    
    stats = stats.sort_values('montant_total', ascending=False).reset_index(drop=True)
    
    return stats


def classifier_clients(stats_clients):
    """
    Classification des clients en 4 profils distincts
    
    Profils:
    1. Premium (top 20% montant total + actif) - renommé (plus de "VIP")
    2. Gros dépensier actif (montant moyen élevé + fréquence élevée)
    3. Client régulier (fréquence moyenne à élevée)
    4. Client occasionnel (tous les autres)
    """
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    # Calcul des seuils basés sur les données REELLES
    percentiles = {
        'freq_high': df['nb_transactions'].quantile(0.75),
        'freq_medium': df['nb_transactions'].quantile(0.50),
        'amount_high': df['montant_moyen'].quantile(0.75),
        'amount_medium': df['montant_moyen'].quantile(0.50),
        'total_high': df['montant_total'].quantile(0.80),  # Top 20%
    }
    
    print(f"\n SEUILS DE CLASSIFICATION (4 profils):")
    print(f"   ┌─────────────────────────────────────────────────┐")
    print(f"   │ Transactions: Haut≥{percentiles['freq_high']:.0f} │ Médian≥{percentiles['freq_medium']:.0f} │")
    print(f"   │ Montant moyen: Haut≥{percentiles['amount_high']:.0f} │ Médian≥{percentiles['amount_medium']:.0f} │")
    print(f"   │ Montant total (Premium): Top 20% ≥{percentiles['total_high']:,.0f} TND │")
    print(f"   └─────────────────────────────────────────────────┘")
    
    def classifier(row):
        # PROFIL 1: Premium (Top 20% montant total) - au lieu de "VIP"
        if row['montant_total'] >= percentiles['total_high']:
            return "Premium"
        
        # Catégories de fréquence pour les autres profils
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
        
        # PROFIL 2: Gros dépensier actif
        if amount_cat == "gros" and freq_cat in ["tres_actif", "actif"]:
            return "Gros dépensier actif"
        
        # PROFIL 3: Client régulier
        if freq_cat in ["tres_actif", "actif"]:
            return "Client régulier"
        
        # PROFIL 4: Client occasionnel
        return "Client occasionnel"
    
    df['profil'] = df.apply(classifier, axis=1)
    
    # Vérification des profils
    profil_counts = df['profil'].value_counts()
    print(f"\n RÉPARTITION DES 4 PROFILS:")
    print(f"   ┌─────────────────────────────────────────────────────┐")
    for profil, count in profil_counts.items():
        pourcentage = count / len(df) * 100
        barre = "█" * int(pourcentage / 2)
        print(f"   │ {profil:<20} │ {count:>4} clients │ {pourcentage:>5.1f}% │ {barre}")
    print(f"   └─────────────────────────────────────────────────────┘")
    
    return df


def generer_recommandations(stats_clients, df_transactions, df_trans_types=None):
    """
    Génère des recommandations personnalisées pour les 4 profils
    """
    if len(stats_clients) == 0:
        return pd.DataFrame()
    
    recommendations = []
    
    # Mapping des recommandations par profil (sans "VIP")
    rec_mapping = {
        "Premium": {
            'rec1': " Programme fidélité Premium - Cashback majoré à 5% sur toutes les transactions",
            'rec2': " Accès exclusif aux offres partenaires (restaurants, hôtels, voyages)",
            'rec3': " Conseiller financier dédié avec analyse personnalisée",
            'alert': " Objectif : Maintenez votre statut Premium avec >5000 TND/mois",
            'type': 'premium'
        },
        "Gros dépensier actif": {
            'rec1': " Cashback 3% sur vos 3 catégories de dépenses favorites",
            'rec2': " Offres personnalisées basées sur votre historique d'achats",
            'rec3': " Rapport mensuel détaillé avec analyse des tendances",
            'alert': " Objectif Premium : Atteignez 5000 TND/mois pour débloquer le statut Premium",
            'type': 'premium'
        },
        "Client régulier": {
            'rec1': " Programme de parrainage - Gagnez 50 TND par ami parrainé",
            'rec2': " Catégories suggérées pour optimiser votre cashback quotidien",
            'rec3': " Budget personnalisé basé sur vos habitudes de consommation",
            'alert': " Effectuez 3 transactions par semaine pour +50% de cashback",
            'type': 'fidelisation'
        },
        "Client occasionnel": {
            'rec1': " 50 TND offerts pour votre prochaine transaction",
            'rec2': " Découvrez les fonctionnalités du wallet mobile",
            'rec3': " Cashback 5% pendant les 3 premiers mois",
            'alert': " Activez votre wallet dès aujourd'hui pour débloquer tous les avantages",
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
    
    print(f"\n   {len(recommendations)} recommandations générées")
    return pd.DataFrame(recommendations)


def calculer_statistiques_providers(df_transactions_clients, df_providers):
    """Calcule les statistiques pour chaque fournisseur"""
    if len(df_transactions_clients) == 0 or len(df_providers) == 0:
        return pd.DataFrame()
    
    if 'provider_id' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    if 'amount' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    stats = df_transactions_clients.groupby('provider_id').agg({
        'amount': ['count', 'sum', 'mean'],
        'client_id': 'nunique'
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen', 'nb_clients']
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    if len(df_providers) > 0:
        # Trouver la colonne ID du provider
        provider_col = df_providers.columns[0]
        stats = stats.merge(df_providers[[provider_col]], left_on='provider_id', right_on=provider_col, how='left')
    
    return stats


def classifier_providers(stats_providers):
    """
    Classification des fournisseurs en catégories
    
    Cette fonction est appelée dans main.py
    """
    if len(stats_providers) == 0:
        return stats_providers
    
    df = stats_providers.copy()
    
    if len(df) > 0:
        # Calcul des seuils pour la classification des providers
        seuil_transactions = df['nb_transactions'].quantile(0.75)
        seuil_montant = df['montant_total'].quantile(0.75)
        
        print(f"\n  SEUILS DE CLASSIFICATION FOURNISSEURS:")
        print(f"   ┌─────────────────────────────────────────────────┐")
        print(f"   │ Transactions: Haut≥{seuil_transactions:.0f} transactions")
        print(f"   │ Montant total: Haut≥{seuil_montant:,.2f} TND")
        print(f"   └─────────────────────────────────────────────────┘")
        
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
        
        # Afficher la répartition
        print(f"\n RÉPARTITION DES FOURNISSEURS:")
        print(f"   ┌─────────────────────────────────────────────────────┐")
        profil_counts = df['profil_provider'].value_counts()
        for profil, count in profil_counts.items():
            pourcentage = count / len(df) * 100
            print(f"   │ {profil:<35} │ {count:>3} ({pourcentage:.1f}%) │")
        print(f"   └─────────────────────────────────────────────────────┘")
    
    return df