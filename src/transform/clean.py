import pandas as pd

def nettoyer_transactions(df):
    """Nettoie la table des transactions"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Identifier les colonnes importantes
    amount_col = None
    date_col = None
    client_id_col = None
    provider_id_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'amount' in col_lower or 'montant' in col_lower:
            amount_col = col
        elif 'date' in col_lower:
            date_col = col
        elif 'client' in col_lower and 'id' in col_lower:
            client_id_col = col
        elif 'provider' in col_lower and 'id' in col_lower:
            provider_id_col = col
    
    # Renommer les colonnes
    if amount_col and amount_col != 'amount':
        df = df.rename(columns={amount_col: 'amount'})
    if date_col and date_col != 'transaction_date':
        df = df.rename(columns={date_col: 'transaction_date'})
    if client_id_col and client_id_col != 'client_id':
        df = df.rename(columns={client_id_col: 'client_id'})
    if provider_id_col and provider_id_col != 'provider_id':
        df = df.rename(columns={provider_id_col: 'provider_id'})
    
    # =========================================================
    # 🔧 CORRECTION POWER BI : Remplacer \N par des valeurs vides
    # =========================================================
    # Remplacer \N par None (NULL) dans tout le DataFrame
    df = df.replace('\\N', None)
    df = df.replace('\\N', pd.NA)
    
    # Pour les colonnes de type texte, remplacer les NaN par chaîne vide
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('')
    
    # Convertir les types
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    # Filtrer les valeurs aberrantes
    if 'amount' in df.columns:
        df = df[df['amount'] > 0]
        df = df[df['amount'] < 1000000]  # Supprimer les montants > 1 million
    
    # Nettoyer les dates
    if 'transaction_date' in df.columns:
        df = df.dropna(subset=['transaction_date'])
        
        # Ajouter des colonnes temporelles
        df['annee'] = df['transaction_date'].dt.year
        df['mois'] = df['transaction_date'].dt.month
        df['jour'] = df['transaction_date'].dt.day
        df['jour_semaine'] = df['transaction_date'].dt.day_name()
        df['mois_annee'] = df['transaction_date'].dt.to_period('M').astype(str)
    
    # Supprimer les doublons
    df = df.drop_duplicates()
    
    # Nettoyer les IDs clients
    if 'client_id' in df.columns:
        df['client_id'] = df['client_id'].astype(str).str.strip()
        df['client_id'] = df['client_id'].fillna('INCONNU')
    
    # Nettoyer les IDs providers
    if 'provider_id' in df.columns:
        df['provider_id'] = df['provider_id'].astype(str).str.strip()
        df['provider_id'] = df['provider_id'].fillna('INTERNE_WALLET')
    
    # Vérification des colonnes requises
    colonnes_requises = ['amount', 'client_id']
    for col in colonnes_requises:
        if col not in df.columns:
            print(f" ATTENTION: Colonne '{col}' non trouvée dans les transactions")
    
    return df

def nettoyer_clients(df):
    """Nettoie la table des clients"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Remplacer \N par des valeurs vides
    df = df.replace('\\N', None)
    df = df.replace('\\N', pd.NA)
    
    df = df.drop_duplicates()
    
    # Nettoyer les numéros de téléphone
    phone_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'phone' in col_lower or 'telephone' in col_lower or 'numero' in col_lower:
            phone_col = col
            break
    
    if phone_col:
        df[phone_col] = df[phone_col].astype(str)
        df[phone_col] = df[phone_col].str.replace(r'[^0-9+]', '', regex=True)
        df[phone_col] = df[phone_col].apply(lambda x: x if len(x) >= 8 else None)
    
    # Supprimer les lignes sans ID
    id_col = df.columns[0]
    df = df[df[id_col].notna()]
    df[id_col] = df[id_col].astype(str).str.strip()
    df[id_col] = df[id_col].fillna('INCONNU')
    
    # Remplacer les NaN restants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('')
    
    return df

def nettoyer_providers(df):
    """Nettoie la table des providers"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Remplacer \N par des valeurs vides
    df = df.replace('\\N', None)
    df = df.replace('\\N', pd.NA)
    
    df = df.drop_duplicates()
    
    # Nettoyer les noms
    name_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'name' in col_lower or 'nom' in col_lower or 'libelle' in col_lower:
            name_col = col
            break
    
    if name_col:
        df[name_col] = df[name_col].fillna('Fournisseur inconnu')
        df[name_col] = df[name_col].astype(str).str.strip()
        df[name_col] = df[name_col].replace('\\N', 'INTERNE_WALLET')
    
    # Supprimer les lignes sans ID
    id_col = df.columns[0]
    df = df[df[id_col].notna()]
    df[id_col] = df[id_col].astype(str).str.strip()
    df[id_col] = df[id_col].fillna('INTERNE_WALLET')
    
    # Remplacer les NaN restants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('')
    
    return df

def nettoyer_transaction_types(df):
    """Nettoie la table des types de transactions"""
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    # Remplacer \N par des valeurs vides
    df = df.replace('\\N', None)
    df = df.replace('\\N', pd.NA)
    
    df = df.drop_duplicates()
    
    # Nettoyer les codes
    code_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'code' in col_lower:
            code_col = col
            break
    
    if code_col:
        df = df[df[code_col].notna()]
        df[code_col] = df[code_col].astype(str).str.upper().str.strip()
        df[code_col] = df[code_col].fillna('')
    
    # Remplacer les NaN restants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('')
    
    return df

def fusionner_avec_referentiels(df_trans, df_clients, df_providers):
    """Fusionne les transactions avec les référentiels"""
    if len(df_trans) == 0:
        return df_trans
    
    df = df_trans.copy()
    
    # Identifier les IDs clients
    ids_clients = set()
    if len(df_clients) > 0:
        ids_clients = set(df_clients[df_clients.columns[0]].astype(str).values)
    
    # Marquer les transactions clients
    if 'client_id' in df.columns:
        df['est_client'] = df['client_id'].astype(str).apply(
            lambda x: x in ids_clients if pd.notna(x) else False
        )
    
    return df

def garder_transactions_clients(df):
    """Garde uniquement les transactions des clients"""
    if 'est_client' in df.columns:
        return df[df['est_client'] == True].copy()
    return df

def garder_transactions_providers(df):
    """Garde toutes les transactions pour l'analyse des providers"""
    return df.copy() if len(df) > 0 else pd.DataFrame()