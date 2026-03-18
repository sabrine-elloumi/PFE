import pandas as pd

def nettoyer_transactions(df):
    """Nettoie les donnees des transactions"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Conversion des types
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    # Filtrage des valeurs aberrantes
    df = df[df['amount'] > 0]
    df = df[df['amount'] < 1000000]
    df = df.dropna(subset=['transaction_date'])
    
    # Ajout de colonnes temporelles
    df['annee'] = df['transaction_date'].dt.year
    df['mois'] = df['transaction_date'].dt.month
    df['jour'] = df['transaction_date'].dt.day
    df['jour_semaine'] = df['transaction_date'].dt.day_name()
    df['mois_annee'] = df['transaction_date'].dt.to_period('M')
    
    return df

def fusionner_avec_clients(df_trans, df_clients):
    """Fusionne les transactions avec les donnees clients"""
    if len(df_clients) > 0:
        return pd.merge(
            df_trans,
            df_clients[['id', 'phone_number', 'first_name', 'last_name']],
            left_on='client_id',
            right_on='id',
            how='left'
        )
    else:
        df_trans['phone_number'] = 'Inconnu'
        return df_trans