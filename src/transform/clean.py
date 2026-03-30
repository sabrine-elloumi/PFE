import pandas as pd

def nettoyer_transactions(df):
    if len(df) == 0:
        return df
    
    df = df.copy()
    
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
    
    if amount_col and amount_col != 'amount':
        df = df.rename(columns={amount_col: 'amount'})
    if date_col and date_col != 'transaction_date':
        df = df.rename(columns={date_col: 'transaction_date'})
    if client_id_col and client_id_col != 'client_id':
        df = df.rename(columns={client_id_col: 'client_id'})
    if provider_id_col and provider_id_col != 'provider_id':
        df = df.rename(columns={provider_id_col: 'provider_id'})
    
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    if 'amount' in df.columns:
        df = df[df['amount'] > 0]
        df = df[df['amount'] < 1000000]
    
    if 'transaction_date' in df.columns:
        df = df.dropna(subset=['transaction_date'])
        
        df['annee'] = df['transaction_date'].dt.year
        df['mois'] = df['transaction_date'].dt.month
        df['jour'] = df['transaction_date'].dt.day
        df['jour_semaine'] = df['transaction_date'].dt.day_name()
        df['mois_annee'] = df['transaction_date'].dt.to_period('M')
    
    df = df.drop_duplicates()
    
    return df


def nettoyer_clients(df):
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    df = df.drop_duplicates()
    
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
    
    id_col = df.columns[0]
    df = df[df[id_col].notna()]
    
    return df


def nettoyer_providers(df):
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    df = df.drop_duplicates()
    
    name_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'name' in col_lower or 'nom' in col_lower or 'libelle' in col_lower:
            name_col = col
            break
    
    if name_col:
        df[name_col] = df[name_col].fillna('Fournisseur inconnu')
        df[name_col] = df[name_col].astype(str).str.strip()
    
    id_col = df.columns[0]
    df = df[df[id_col].notna()]
    
    return df


def nettoyer_transaction_types(df):
    if len(df) == 0:
        return df
    
    df = df.copy()
    
    df = df.drop_duplicates()
    
    code_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'code' in col_lower:
            code_col = col
            break
    
    if code_col:
        df = df[df[code_col].notna()]
        df[code_col] = df[code_col].astype(str).str.upper().str.strip()
    
    label_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'label' in col_lower or 'libelle' in col_lower:
            label_col = col
            break
    
    if label_col:
        df[label_col] = df[label_col].fillna('')
        df[label_col] = df[label_col].astype(str).str.strip()
    
    return df


def fusionner_avec_referentiels(df_trans, df_clients, df_providers):
    if len(df_trans) == 0:
        return df_trans
    
    df = df_trans.copy()
    
    ids_clients = set()
    if len(df_clients) > 0:
        ids_clients = set(df_clients[df_clients.columns[0]].astype(str).values)
    
    ids_providers = set()
    if len(df_providers) > 0:
        ids_providers = set(df_providers[df_providers.columns[0]].astype(str).values)
    
    overlap = ids_clients.intersection(ids_providers)
    if overlap:
        print(f"   Attention: {len(overlap)} IDs sont a la fois clients et providers")
        ids_providers = ids_providers - overlap
    
    if 'client_id' in df.columns:
        df['est_client'] = df['client_id'].astype(str).apply(
            lambda x: x in ids_clients if pd.notna(x) else False
        )
    
    if 'provider_id' in df.columns:
        df['est_provider'] = df['provider_id'].astype(str).apply(
            lambda x: x in ids_providers if pd.notna(x) else False
        )
    
    return df


def garder_transactions_clients(df):
    if 'est_client' in df.columns:
        return df[df['est_client'] == True].copy()
    return df


def garder_transactions_providers(df):
    if 'est_provider' in df.columns:
        return df[df['est_provider'] == True].copy()
    return pd.DataFrame()