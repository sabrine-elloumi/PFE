import pandas as pd
import numpy as np

def calculer_statistiques_clients(df_transactions_clients):
    """
    Calcule les statistiques par client avec indicateurs avancés
    """
    if len(df_transactions_clients) == 0:
        return pd.DataFrame()
    
    # Vérifier les colonnes disponibles
    if 'client_id' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    if 'amount' not in df_transactions_clients.columns:
        return pd.DataFrame()
    
    stats = df_transactions_clients.groupby('client_id').agg({
        'amount': ['count', 'sum', 'mean', 'std', 'min', 'max'],
        'transaction_date': ['min', 'max', 'count']
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen', 
                     'ecart_type', 'montant_min', 'montant_max',
                     'premiere_transaction', 'derniere_transaction', '_']
    
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    # Calculer la régularité (nombre de jours entre première et dernière)
    stats['duree_activite_jours'] = (stats['derniere_transaction'] - stats['premiere_transaction']).dt.days
    stats['frequence_mensuelle'] = stats['nb_transactions'] / (stats['duree_activite_jours'] / 30).clip(lower=0.1)
    
    # Calculer le coefficient de variation (volatilité)
    stats['coefficient_variation'] = stats['ecart_type'] / stats['montant_moyen'].clip(lower=0.01)
    stats['coefficient_variation'] = stats['coefficient_variation'].fillna(0)
    
    # Recency (jours depuis la dernière transaction)
    today = df_transactions_clients['transaction_date'].max()
    stats['recence_jours'] = (today - stats['derniere_transaction']).dt.days
    
    return stats

def classifier_clients(stats_clients):
    """
    Classifie les clients en 6 profils pour recommandations personnalisées
    (Version principale avec 6 profils)
    
    Profils:
    1. VIP - Très actifs, gros montants, réguliers
    2. Gros dépensiers réguliers - Montants élevés, fréquence élevée
    3. Gros dépensiers occasionnels - Montants élevés, fréquence faible
    4. Clients réguliers modérés - Fréquence élevée, montants modérés
    5. Petits dépensiers réguliers - Fréquence élevée, petits montants
    6. Clients occasionnels - Faible fréquence, petits montants
    """
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    # Calcul des seuils avec percentiles pour plus de précision
    percentiles = {
        'freq_high': df['nb_transactions'].quantile(0.75),  # 75e percentile
        'freq_medium': df['nb_transactions'].quantile(0.50),  # Médiane
        'freq_low': df['nb_transactions'].quantile(0.25),  # 25e percentile
        'amount_high': df['montant_moyen'].quantile(0.75),
        'amount_medium': df['montant_moyen'].quantile(0.50),
        'amount_low': df['montant_moyen'].quantile(0.25),
        'total_high': df['montant_total'].quantile(0.75),
    }
    
    print(f"\n   📊 SEUILS DE CLASSIFICATION (6 profils):")
    print(f"   Fréquence: Haut={percentiles['freq_high']:.0f}, Médian={percentiles['freq_medium']:.0f}, Bas={percentiles['freq_low']:.0f}")
    print(f"   Montant moyen: Haut={percentiles['amount_high']:.2f}, Médian={percentiles['amount_medium']:.2f}, Bas={percentiles['amount_low']:.2f}")
    print(f"   Montant total haut: {percentiles['total_high']:,.2f}")
    
    def classifier(row):
        # Catégorie fréquence
        if row['nb_transactions'] >= percentiles['freq_high']:
            freq_cat = "tres_actif"
        elif row['nb_transactions'] >= percentiles['freq_medium']:
            freq_cat = "actif"
        else:
            freq_cat = "occasionnel"
        
        # Catégorie montant
        if row['montant_moyen'] >= percentiles['amount_high']:
            amount_cat = "gros"
        elif row['montant_moyen'] >= percentiles['amount_medium']:
            amount_cat = "modere"
        else:
            amount_cat = "petit"
        
        # Détection des VIP (top 10% par montant total)
        is_vip = row['montant_total'] >= percentiles['total_high']
        
        # Règle spéciale pour les très gros montants totaux
        if is_vip and row['nb_transactions'] >= percentiles['freq_medium']:
            return "VIP (Clients Premium)"
        
        # Classification standard
        if freq_cat == "tres_actif" and amount_cat == "gros":
            return "Gros dépensier régulier (Premium)"
        elif freq_cat == "tres_actif" and amount_cat == "modere":
            return "Client régulier modéré (Actif)"
        elif freq_cat == "tres_actif" and amount_cat == "petit":
            return "Micro-transactionneur (Fidèle)"
        elif freq_cat == "actif" and amount_cat == "gros":
            return "Gros dépensier occasionnel"
        elif freq_cat == "actif" and amount_cat == "modere":
            return "Client standard (Actif modéré)"
        elif freq_cat == "actif" and amount_cat == "petit":
            return "Petit dépensier régulier"
        elif freq_cat == "occasionnel" and amount_cat == "gros":
            return "Gros dépensier rare (Occasionnel)"
        elif freq_cat == "occasionnel" and amount_cat == "modere":
            return "Client occasionnel modéré"
        else:
            return "Client occasionnel (Petits montants)"
    
    df['profil'] = df.apply(classifier, axis=1)
    
    # Ajout de métadonnées pour les recommandations
    df['recommandation_priority'] = df['profil'].map({
        "VIP (Clients Premium)": 1,
        "Gros dépensier régulier (Premium)": 1,
        "Gros dépensier occasionnel": 2,
        "Client régulier modéré (Actif)": 2,
        "Client standard (Actif modéré)": 3,
        "Micro-transactionneur (Fidèle)": 3,
        "Petit dépensier régulier": 4,
        "Gros dépensier rare (Occasionnel)": 4,
        "Client occasionnel modéré": 5,
        "Client occasionnel (Petits montants)": 5
    })
    
    return df

def classifier_clients_2_profils(stats_clients):
    """
    Version simplifiée avec 2 profils (pour compatibilité)
    """
    if len(stats_clients) == 0:
        return stats_clients
    
    df = stats_clients.copy()
    
    if len(df) > 0:
        seuil_frequence = df['nb_transactions'].median()
        seuil_montant = df['montant_moyen'].median()
        
        print(f"\n   SEUILS DE CLASSIFICATION (2 profils):")
        print(f"   Seuil de frequence (mediane): {seuil_frequence:.2f} transactions")
        print(f"   Seuil de montant (mediane): {seuil_montant:.2f}")
        
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
    
    return df

def generer_recommandations(stats_clients, df_transactions, df_trans_types=None):
    """
    Génère des recommandations personnalisées pour chaque profil client
    """
    if len(stats_clients) == 0:
        return pd.DataFrame()
    
    df = stats_clients.copy()
    recommendations = []
    
    # Analyse des tendances globales pour contextualiser
    avg_transaction = 0
    if len(df_transactions) > 0 and 'amount' in df_transactions.columns:
        avg_transaction = df_transactions['amount'].mean()
    
    for _, client in df.iterrows():
        profil = client['profil']
        rec = {
            'client_id': client['client_id'],
            'profil': profil,
            'montant_total': client['montant_total'],
            'nb_transactions': client['nb_transactions'],
            'montant_moyen': client['montant_moyen']
        }
        
        # Recommandations basées sur le profil
        if profil == "VIP (Clients Premium)":
            rec.update({
                'recommendation_1': "🏆 Programme fidélité VIP - Accès prioritaire et cashback majoré",
                'recommendation_2': "💎 Offres exclusives partenaires premium (voyages, high-tech)",
                'recommendation_3': "📞 Conseiller dédié et support prioritaire 24/7",
                'recommendation_alert': "Maintenez votre statut VIP avec > 5000 TND/mois",
                'recommandation_type': 'premium'
            })
            
        elif profil == "Gros dépensier régulier (Premium)":
            rec.update({
                'recommendation_1': "🎯 Programme de cashback sur catégories favorites",
                'recommendation_2': "⭐ Offres personnalisées sur vos commerces préférés",
                'recommendation_3': "📊 Analyse mensuelle détaillée de vos dépenses",
                'recommendation_alert': "Objectif VIP: +20% de transactions pour accéder au statut VIP",
                'recommandation_type': 'premium'
            })
            
        elif profil == "Gros dépensier occasionnel":
            rec.update({
                'recommendation_1': "💡 Alertes promotions sur vos achats à gros montants",
                'recommendation_2': "🎁 Offres de fidélisation pour augmenter votre fréquence",
                'recommendation_3': "📅 Planification d'achats pour optimiser le budget",
                'recommendation_alert': f"Vous pourriez économiser 15% en programmant vos gros achats (moyenne: {client['montant_moyen']:.0f} TND)",
                'recommandation_type': 'engagement'
            })
            
        elif profil == "Client régulier modéré (Actif)":
            rec.update({
                'recommendation_1': "📈 Programme de parrainage - Gagnez 50 TND par filleul",
                'recommendation_2': "🎯 Catégories suggérées basées sur vos habitudes",
                'recommendation_3': "📊 Budget personnalisé avec objectifs mensuels",
                'recommendation_alert': "Augmentez votre fréquence pour accéder aux offres premium",
                'recommandation_type': 'fidelisation'
            })
            
        elif profil == "Client standard (Actif modéré)":
            rec.update({
                'recommendation_1': "💳 Cashback 1% sur toutes les transactions",
                'recommendation_2': "📱 Notifications personnalisées sur les promotions",
                'recommendation_3': "🎯 Défis d'épargne personnalisés",
                'recommendation_alert': "3 transactions par semaine = +50% de cashback",
                'recommandation_type': 'standard'
            })
            
        elif profil == "Micro-transactionneur (Fidèle)":
            rec.update({
                'recommendation_1': "🔄 Programme de fidélité sur petits achats quotidiens",
                'recommendation_2': "☕ Offres exclusives sur commerces de proximité",
                'recommendation_3': "📊 Visualisation des petites dépenses cumulées",
                'recommendation_alert': "Vos {client['nb_transactions']} transactions cumulées représentent {client['montant_total']:.0f} TND",
                'recommandation_type': 'fidelisation'
            })
            
        elif profil == "Petit dépensier régulier":
            rec.update({
                'recommendation_1': "🎯 Défis épargne: Économisez 50 TND par mois",
                'recommendation_2': "📚 Conseils financiers pour petits budgets",
                'recommendation_3': "⭐ Récompenses pour régularité de paiement",
                'recommendation_alert': "Augmentez vos transactions pour débloquer des récompenses",
                'recommandation_type': 'education'
            })
            
        elif profil == "Gros dépensier rare (Occasionnel)":
            rec.update({
                'recommendation_1': "📅 Alertes avant achats importants",
                'recommendation_2': "💰 Simulation financement pour gros achats",
                'recommendation_3': "🏷️ Alertes soldes et promotions sur catégories visées",
                'recommendation_alert': "Planifiez vos gros achats pour bénéficier des meilleures offres",
                'recommandation_type': 'engagement'
            })
            
        elif profil in ["Client occasionnel modéré", "Client occasionnel (Petits montants)"]:
            rec.update({
                'recommendation_1': "🎁 50 TND offerts pour votre première transaction",
                'recommendation_2': "📱 Découvrez les fonctionnalités du wallet",
                'recommendation_3': "⭐ Programme de bienvenue: cashback 5% sur 3 mois",
                'recommendation_alert': "Activez votre wallet pour bénéficier des avantages",
                'recommandation_type': 'acquisition'
            })
            
        else:  # Autres profils (2 profils legacy)
            rec.update({
                'recommendation_1': "🎁 Découvrez nos offres personnalisées",
                'recommendation_2': "📊 Analyse de vos dépenses mensuelles",
                'recommendation_3': "⭐ Programme de fidélité à venir",
                'recommendation_alert': "Utilisez plus souvent votre wallet pour débloquer des avantages",
                'recommandation_type': 'standard'
            })
        
        recommendations.append(rec)
    
    return pd.DataFrame(recommendations)

def calculer_statistiques_agents(df_transactions_agents):
    """
    Calcule les statistiques par agent
    """
    if len(df_transactions_agents) == 0:
        return pd.DataFrame()
    
    if 'agent_id' not in df_transactions_agents.columns:
        return pd.DataFrame()
    
    if 'amount' not in df_transactions_agents.columns:
        return pd.DataFrame()
    
    stats = df_transactions_agents.groupby('agent_id').agg({
        'amount': ['count', 'sum', 'mean']
    }).round(2)
    
    stats.columns = ['nb_transactions', 'montant_total', 'montant_moyen']
    stats = stats.reset_index()
    stats = stats[stats['nb_transactions'] > 0]
    
    # Nombre de clients uniques servis par agent
    if 'client_id' in df_transactions_agents.columns:
        clients_par_agent = df_transactions_agents.groupby('agent_id')['client_id'].nunique()
        stats = stats.merge(clients_par_agent.reset_index(), on='agent_id', how='left')
        stats = stats.rename(columns={'client_id': 'nb_clients_servis'})
    
    return stats

def classifier_agents(stats_agents):
    """
    Classifie les agents selon leur volume d'activite
    """
    if len(stats_agents) == 0:
        return stats_agents
    
    df = stats_agents.copy()
    
    if len(df) > 0:
        seuil_transactions = df['nb_transactions'].quantile(0.75)
        seuil_montant = df['montant_total'].quantile(0.75)
        seuil_moyen = df['montant_moyen'].quantile(0.75)
        
        print(f"\n   SEUILS DE CLASSIFICATION AGENTS:")
        print(f"   Seuil transactions (75e): {seuil_transactions:.0f} transactions")
        print(f"   Seuil montant (75e): {seuil_montant:,.2f}")
        
        def classifier(row):
            if row['nb_transactions'] >= seuil_transactions and row['montant_total'] >= seuil_montant:
                return "Agent Premium (Top performer)"
            elif row['nb_transactions'] >= seuil_transactions and row['montant_moyen'] >= seuil_moyen:
                return "Agent Actif Haut Volume"
            elif row['nb_transactions'] >= seuil_transactions:
                return "Agent Actif (Multi-transactions)"
            elif row['montant_total'] >= seuil_montant:
                return "Agent Occasionnel (Gros montants)"
            else:
                return "Agent Occasionnel (Standard)"
        
        df['profil_agent'] = df.apply(classifier, axis=1)
    
    return df