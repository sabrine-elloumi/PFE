import pandas as pd
import re

def charger_fichier_sql(chemin):
    """Charge le fichier SQL ligne par ligne"""
    with open(chemin, 'r', encoding='utf-8', errors='ignore') as f:
        return f.readlines()

def extraire_clients(lignes):
    """Extrait les donnees des clients du fichier SQL"""
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
        # On ne force pas les colonnes, on prend ce qui est disponible
        max_cols = max(len(row) for row in clients_data)
        df = pd.DataFrame(clients_data)
        # Ajout d'une colonne pour identifier le type
        df['type_utilisateur'] = 'client'
        return df
    return pd.DataFrame()

def extraire_agents(lignes):
    """Extrait les donnees des agents du fichier SQL"""
    agents_data = []
    en_cours = False
    
    for ligne in lignes:
        if "COPY public.agent" in ligne:
            en_cours = True
            continue
        
        if en_cours:
            if ligne.startswith('\\.'):
                break
            elif ligne.strip() and not ligne.startswith('--'):
                valeurs = ligne.strip().split('\t')
                agents_data.append(valeurs)
    
    if agents_data:
        max_cols = max(len(row) for row in agents_data)
        df = pd.DataFrame(agents_data)
        df['type_utilisateur'] = 'agent'
        return df
    return pd.DataFrame()

def extraire_transactions(lignes):
    """Extrait les donnees des transactions du fichier SQL"""
    transactions_data = []
    en_cours = False
    colonnes = None
    
    for i, ligne in enumerate(lignes):
        if "COPY public.transaction" in ligne:
            en_cours = True
            # Extraction des colonnes depuis la ligne COPY
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
        # Ajuster le nombre de colonnes si nécessaire
        df = pd.DataFrame(transactions_data)
        
        # Si le nombre de colonnes ne correspond pas, on essaie de s'adapter
        if len(df.columns) != len(colonnes):
            print(f"   Attention: {len(df.columns)} colonnes dans les donnees, {len(colonnes)} colonnes attendues")
            # On renomme les colonnes de manière générique
            df.columns = [f'col_{i}' for i in range(len(df.columns))]
        else:
            df.columns = colonnes
        
        return df
    elif transactions_data:
        # Si pas de colonnes trouvées, on crée un DataFrame générique
        print("   Attention: Aucune information de colonne trouvee, creation de colonnes generiques")
        df = pd.DataFrame(transactions_data)
        df.columns = [f'col_{i}' for i in range(len(df.columns))]
        return df
    
    return pd.DataFrame()

def extraire_transaction_types(lignes):
    """Extrait les types de transactions du fichier SQL"""
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
        # Trouver le nombre maximum de colonnes dans les donnees
        max_cols = max(len(row) for row in types_data)
        
        # Créer le DataFrame avec des colonnes génériques
        df = pd.DataFrame(types_data)
        
        # Si toutes les lignes ont le même nombre de colonnes, on peut les nommer
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
            # Si les lignes ont des longueurs différentes, on laisse les colonnes génériques
            df.columns = [f'col_{i}' for i in range(max_cols)]
        
        return df
    return pd.DataFrame()

def inferer_colonnes(df_transactions, df_trans_types):
    """
    Infere les noms des colonnes pour les transactions si elles ne sont pas disponibles
    """
    if df_transactions.empty:
        return df_transactions
    
    # Si on a des colonnes génériques, on essaie de les renommer intelligemment
    if all(col.startswith('col_') for col in df_transactions.columns):
        # Chercher les colonnes probables par leur contenu
        col_mapping = {}
        
        for col in df_transactions.columns:
            # Convertir en string pour l'analyse
            sample = df_transactions[col].dropna().astype(str).head(10)
            
            # Détection du type de colonne
            if sample.str.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$').any():
                if 'id' not in col_mapping.values():
                    col_mapping[col] = 'id'
            elif sample.str.match(r'^\d{4}-\d{2}-\d{2}').any():
                col_mapping[col] = 'transaction_date'
            elif sample.str.match(r'^-?\d+\.?\d*$').any():
                if 'amount' not in col_mapping.values():
                    col_mapping[col] = 'amount'
            elif sample.str.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$').any():
                if 'client_id' not in col_mapping.values() and 'agent_id' not in col_mapping.values():
                    col_mapping[col] = 'client_id'
        
        # Renommer les colonnes détectées
        for old_name, new_name in col_mapping.items():
            df_transactions = df_transactions.rename(columns={old_name: new_name})
    
    return df_transactions