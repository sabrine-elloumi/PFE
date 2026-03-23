import pandas as pd

def nettoyer_transactions(df):
    """Nettoie les donnees des transactions"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Identifier la colonne montant
    amount_col = None
    date_col = None
    client_id_col = None
    agent_id_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'amount' in col_lower or 'montant' in col_lower:
            amount_col = col
        elif 'date' in col_lower:
            date_col = col
        elif 'client' in col_lower and 'id' in col_lower:
            client_id_col = col
        elif 'agent' in col_lower and 'id' in col_lower:
            agent_id_col = col
    
    # Renommer les colonnes si nécessaire
    if amount_col and amount_col != 'amount':
        df = df.rename(columns={amount_col: 'amount'})
    if date_col and date_col != 'transaction_date':
        df = df.rename(columns={date_col: 'transaction_date'})
    if client_id_col and client_id_col != 'client_id':
        df = df.rename(columns={client_id_col: 'client_id'})
    if agent_id_col and agent_id_col != 'agent_id':
        df = df.rename(columns={agent_id_col: 'agent_id'})
    
    # Conversion des types
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    # Filtrage des valeurs aberrantes
    if 'amount' in df.columns:
        df = df[df['amount'] > 0]
        df = df[df['amount'] < 1000000]
    
    if 'transaction_date' in df.columns:
        df = df.dropna(subset=['transaction_date'])
        
        # Ajout de colonnes temporelles
        df['annee'] = df['transaction_date'].dt.year
        df['mois'] = df['transaction_date'].dt.month
        df['jour'] = df['transaction_date'].dt.day
        df['jour_semaine'] = df['transaction_date'].dt.day_name()
        df['mois_annee'] = df['transaction_date'].dt.to_period('M')
    
    return df

def fusionner_avec_referentiels(df_trans, df_clients, df_agents):
    """
    Fusionne les transactions avec les referentiels clients et agents
    """
    if len(df_trans) == 0:
        return df_trans
    
    df = df_trans.copy()
    
    # Identifier les IDs des clients et agents
    ids_clients = set()
    if len(df_clients) > 0 and 'id' in df_clients.columns:
        # Si df_clients a une colonne id, on l'utilise
        ids_clients = set(df_clients['id'].astype(str).values)
    elif len(df_clients) > 0:
        # Sinon on prend la première colonne comme ID
        ids_clients = set(df_clients[df_clients.columns[0]].astype(str).values)
    
    ids_agents = set()
    if len(df_agents) > 0 and 'id' in df_agents.columns:
        ids_agents = set(df_agents['id'].astype(str).values)
    elif len(df_agents) > 0:
        ids_agents = set(df_agents[df_agents.columns[0]].astype(str).values)
    
    # Vérification des chevauchements
    overlap = ids_clients.intersection(ids_agents)
    if overlap:
        print(f"   ⚠️ Attention: {len(overlap)} IDs sont a la fois clients et agents")
        ids_agents = ids_agents - overlap
    
    # Ajout des colonnes de distinction
    if 'client_id' in df.columns:
        df['est_client'] = df['client_id'].astype(str).apply(
            lambda x: x in ids_clients if pd.notna(x) else False
        )
    
    if 'agent_id' in df.columns:
        df['est_agent'] = df['agent_id'].astype(str).apply(
            lambda x: x in ids_agents if pd.notna(x) else False
        )
    
    return df

def garder_transactions_clients(df):
    """
    Garde uniquement les transactions où le client_id est un vrai client
    """
    if 'est_client' in df.columns:
        df_clients = df[df['est_client'] == True].copy()
        return df_clients
    return df

def garder_transactions_agents(df):
    """
    Garde uniquement les transactions où l'agent_id est un vrai agent
    """
    if 'est_agent' in df.columns:
        df_agents = df[df['est_agent'] == True].copy()
        return df_agents
    return pd.DataFrame()