import pandas as pd

def calculer_statistiques_clients(df_transactions_clients):
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
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    percentiles = {
        'freq_high': df['nb_transactions'].quantile(0.75),
        'freq_medium': df['nb_transactions'].quantile(0.50),
        'amount_high': df['montant_moyen'].quantile(0.75),
        'amount_medium': df['montant_moyen'].quantile(0.50),
        'total_high': df['montant_total'].quantile(0.75),
    }
    
    print(f"\n   SEUILS DE CLASSIFICATION (6 profils):")
    print(f"   Frequence: Haut={percentiles['freq_high']:.0f}, Median={percentiles['freq_medium']:.0f}")
    print(f"   Montant moyen: Haut={percentiles['amount_high']:.2f}, Median={percentiles['amount_medium']:.2f}")
    
    def classifier(row):
        if row['nb_transactions'] >= percentiles['freq_high']:
            freq_cat = "tres_actif"
        elif row['nb_transactions'] >= percentiles['freq_medium']:
            freq_cat = "actif"
        else:
            freq_cat = "occasionnel"
        
        if row['montant_moyen'] >= percentiles['amount_high']:
            amount_cat = "gros"
        elif row['montant_moyen'] >= percentiles['amount_medium']:
            amount_cat = "modere"
        else:
            amount_cat = "petit"
        
        is_vip = row['montant_total'] >= percentiles['total_high']
        
        if is_vip and row['nb_transactions'] >= percentiles['freq_medium']:
            return "VIP (Clients Premium)"
        elif freq_cat == "tres_actif" and amount_cat == "gros":
            return "Gros depensier regulier (Premium)"
        elif freq_cat == "tres_actif" and amount_cat == "modere":
            return "Client regulier modere (Actif)"
        elif freq_cat == "tres_actif" and amount_cat == "petit":
            return "Micro-transactionneur (Fidele)"
        elif freq_cat == "actif" and amount_cat == "gros":
            return "Gros depensier occasionnel"
        elif freq_cat == "actif" and amount_cat == "modere":
            return "Client standard (Actif modere)"
        elif freq_cat == "actif" and amount_cat == "petit":
            return "Petit depensier regulier"
        elif freq_cat == "occasionnel" and amount_cat == "gros":
            return "Gros depensier rare (Occasionnel)"
        else:
            return "Client occasionnel"
    
    df['profil'] = df.apply(classifier, axis=1)
    
    return df

def generer_recommandations(stats_clients, df_transactions, df_trans_types=None):
    if len(stats_clients) == 0:
        return pd.DataFrame()
    
    recommendations = []
    
    for _, client in stats_clients.iterrows():
        profil = client['profil']
        rec = {
            'client_id': client['client_id'],
            'profil': profil,
            'montant_total': client['montant_total'],
            'nb_transactions': client['nb_transactions'],
            'montant_moyen': client['montant_moyen']
        }
        
        if profil == "VIP (Clients Premium)":
            rec.update({
                'recommendation_1': "Programme fidelite VIP - Cashback majore",
                'recommendation_2': "Offres exclusives partenaires premium",
                'recommendation_3': "Conseiller dedie 24/7",
                'recommendation_alert': "Maintenez votre statut VIP avec plus de 5000 TND/mois",
                'recommandation_type': 'premium'
            })
        elif profil == "Gros depensier regulier (Premium)":
            rec.update({
                'recommendation_1': "Cashback sur categories favorites",
                'recommendation_2': "Offres personnalisees",
                'recommendation_3': "Analyse mensuelle detaillee",
                'recommendation_alert': "Objectif VIP: +20% de transactions",
                'recommandation_type': 'premium'
            })
        elif profil == "Gros depensier occasionnel":
            rec.update({
                'recommendation_1': "Alertes promotions gros achats",
                'recommendation_2': "Offres de fidelisation",
                'recommendation_3': "Planification d'achats",
                'recommendation_alert': f"Economisez 15% en programmant vos achats (moyenne: {client['montant_moyen']:.0f} TND)",
                'recommandation_type': 'engagement'
            })
        elif profil == "Client regulier modere (Actif)":
            rec.update({
                'recommendation_1': "Parrainage - Gagnez 50 TND par filleul",
                'recommendation_2': "Categories suggerees",
                'recommendation_3': "Budget personnalise",
                'recommendation_alert': "Augmentez votre frequence pour acceder aux offres premium",
                'recommandation_type': 'fidelisation'
            })
        elif profil == "Client standard (Actif modere)":
            rec.update({
                'recommendation_1': "Cashback 1% sur toutes transactions",
                'recommendation_2': "Notifications promotions",
                'recommendation_3': "Defis d'epargne",
                'recommendation_alert': "3 transactions par semaine = +50% cashback",
                'recommandation_type': 'standard'
            })
        elif profil == "Micro-transactionneur (Fidele)":
            rec.update({
                'recommendation_1': "Fidelite petits achats quotidiens",
                'recommendation_2': "Offres commerces de proximite",
                'recommendation_3': "Visualisation depenses cumulees",
                'recommendation_alert': f"{client['nb_transactions']} transactions cumulees = {client['montant_total']:.0f} TND",
                'recommandation_type': 'fidelisation'
            })
        elif profil == "Petit depensier regulier":
            rec.update({
                'recommendation_1': "Defis epargne: Economisez 50 TND par mois",
                'recommendation_2': "Conseils financiers pour petits budgets",
                'recommendation_3': "Recompenses pour regularite",
                'recommendation_alert': "Augmentez vos transactions pour plus de recompenses",
                'recommandation_type': 'education'
            })
        elif profil == "Gros depensier rare (Occasionnel)":
            rec.update({
                'recommendation_1': "Alertes avant achats importants",
                'recommendation_2': "Simulation financement",
                'recommendation_3': "Alertes soldes",
                'recommendation_alert': "Planifiez vos gros achats pour meilleures offres",
                'recommandation_type': 'engagement'
            })
        elif profil == "Client occasionnel":
            rec.update({
                'recommendation_1': "50 TND offerts premiere transaction",
                'recommendation_2': "Decouvrez le wallet",
                'recommendation_3': "Cashback 5% sur 3 mois",
                'recommendation_alert': "Activez votre wallet pour beneficier des avantages",
                'recommandation_type': 'acquisition'
            })
        else:
            rec.update({
                'recommendation_1': "Decouvrez nos offres personnalisees",
                'recommendation_2': "Analyse de vos depenses mensuelles",
                'recommendation_3': "Programme de fidelite a venir",
                'recommendation_alert': "Utilisez plus souvent votre wallet",
                'recommandation_type': 'standard'
            })
        
        recommendations.append(rec)
    
    return pd.DataFrame(recommendations)

def calculer_statistiques_providers(df_transactions_clients, df_providers):
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
        provider_col = df_providers.columns[0]
        stats = stats.merge(df_providers[[provider_col]], left_on='provider_id', right_on=provider_col, how='left')
    
    return stats

def classifier_providers(stats_providers):
    if len(stats_providers) == 0:
        return stats_providers
    
    df = stats_providers.copy()
    
    if len(df) > 0:
        seuil_transactions = df['nb_transactions'].quantile(0.75)
        seuil_montant = df['montant_total'].quantile(0.75)
        
        print(f"\n   SEUILS DE CLASSIFICATION FOURNISSEURS:")
        print(f"   Seuil transactions: {seuil_transactions:.0f} transactions")
        print(f"   Seuil montant: {seuil_montant:,.2f}")
        
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
    
    return df
   