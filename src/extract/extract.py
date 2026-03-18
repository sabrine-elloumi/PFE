import pandas as pd

def extraire_clients(lignes):
    """Extrait les donnees des clients du fichier SQL"""
    clients_data = []
    en_cours = False
    
    for i, ligne in enumerate(lignes):
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
        colonnes = ['id', 'created_by', 'create_date_time', 'modified_by', 
                   'modified_date_time', 'first_name', 'identity', 
                   'last_name', 'phone_number', 'uuid']
        return pd.DataFrame(clients_data, columns=colonnes[:len(clients_data[0])])
    return pd.DataFrame()

def extraire_transactions(lignes):
    """Extrait les donnees des transactions du fichier SQL"""
    transactions_data = []
    en_cours = False
    colonnes = []
    
    for i, ligne in enumerate(lignes):
        if "COPY public.transaction" in ligne:
            en_cours = True
            colonnes_part = ligne[ligne.find('(')+1:ligne.find(')')]
            colonnes = [c.strip() for c in colonnes_part.split(',')]
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                if len(valeurs) == len(colonnes):
                    transactions_data.append(valeurs)
    
    if transactions_data:
        return pd.DataFrame(transactions_data, columns=colonnes)
    return pd.DataFrame()

def charger_fichier_sql(chemin):
    """Charge le fichier SQL ligne par ligne"""
    with open(chemin, 'r', encoding='utf-8', errors='ignore') as f:
        return f.readlines()