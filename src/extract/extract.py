import pandas as pd
import re

def charger_fichier_sql(chemin):
    with open(chemin, 'r', encoding='utf-8', errors='ignore') as f:
        return f.readlines()

def extraire_clients(lignes):
    clients_data = []
    en_cours = False
    
    for ligne in lignes:
        if "COPY public.client" in ligne:
            en_cours = True
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                clients_data.append(valeurs)
    
    if clients_data:
        df = pd.DataFrame(clients_data)
        df['type'] = 'client'
        return df
    return pd.DataFrame()

def extraire_providers(lignes):
    providers_data = []
    en_cours = False
    
    for ligne in lignes:
        if "COPY public.provider" in ligne:
            en_cours = True
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                providers_data.append(valeurs)
    
    if providers_data:
        df = pd.DataFrame(providers_data)
        df['type'] = 'provider'
        return df
    return pd.DataFrame()

def extraire_transactions(lignes):
    transactions_data = []
    en_cours = False
    colonnes = None
    
    for i, ligne in enumerate(lignes):
        if "COPY public.transaction" in ligne:
            en_cours = True
            match = re.search(r'\((.*?)\)', ligne)
            if match:
                colonnes_str = match.group(1)
                colonnes = [c.strip() for c in colonnes_str.split(',')]
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                transactions_data.append(valeurs)
    
    if transactions_data and colonnes:
        df = pd.DataFrame(transactions_data)
        if len(df.columns) != len(colonnes):
            df.columns = [f'col_{i}' for i in range(len(df.columns))]
        else:
            df.columns = colonnes
        return df
    elif transactions_data:
        df = pd.DataFrame(transactions_data)
        df.columns = [f'col_{i}' for i in range(len(df.columns))]
        return df
    
    return pd.DataFrame()

def extraire_transaction_types(lignes):
    types_data = []
    en_cours = False
    
    for ligne in lignes:
        if "COPY public.transaction_type" in ligne:
            en_cours = True
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                types_data.append(valeurs)
    
    if types_data:
        max_cols = max(len(row) for row in types_data)
        df = pd.DataFrame(types_data)
        
        if all(len(row) == max_cols for row in types_data):
            if max_cols == 5:
                df.columns = ['id', 'code', 'label', 'type', 'description']
            elif max_cols == 4:
                df.columns = ['id', 'code', 'label', 'type']
            elif max_cols == 3:
                df.columns = ['id', 'code', 'label']
            else:
                df.columns = [f'col_{i}' for i in range(max_cols)]
        else:
            df.columns = [f'col_{i}' for i in range(max_cols)]
        
        return df
    return pd.DataFrame()