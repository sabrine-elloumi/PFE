import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

print("ETL - SMART PERSONAL FINANCE WALLET")
print("")

# Lecture du fichier SQL
print("Lecture du fichier SQL...")

with open('izitransactionmanager.sql', 'r', encoding='utf-8', errors='ignore') as f:
    lignes = f.readlines()

print(f"Fichier charge: {len(lignes)} lignes")
print("")

# Extraction des clients
print("Extraction des clients...")

clients_data = []
en_cours_clients = False

for i, ligne in enumerate(lignes):
    if "COPY public.client" in ligne:
        en_cours_clients = True
        print(f"  Debut des clients a la ligne {i+1}")
        continue
    
    if en_cours_clients:
        if ligne.startswith('\\.'):
            en_cours_clients = False
            print(f"  Fin des clients a la ligne {i+1}")
            break
        elif ligne.strip() and not ligne.startswith('--'):
            valeurs = ligne.strip().split('\t')
            clients_data.append(valeurs)

print(f"  {len(clients_data)} clients trouves")
print("")

# Extraction des transactions
print("Extraction des transactions...")

transactions_data = []
en_cours_transactions = False

for i, ligne in enumerate(lignes):
    if "COPY public.transaction" in ligne:
        en_cours_transactions = True
        print(f"  Debut des transactions a la ligne {i+1}")
        colonnes_part = ligne[ligne.find('(')+1:ligne.find(')')]
        colonnes = [c.strip() for c in colonnes_part.split(',')]
        print(f"  {len(colonnes)} colonnes trouvees")
        continue
    
    if en_cours_transactions:
        if ligne.startswith('\\.'):
            en_cours_transactions = False
            print(f"  Fin des transactions a la ligne {i+1}")
            break
        elif ligne.strip() and not ligne.startswith('--'):
            valeurs = ligne.strip().split('\t')
            if len(valeurs) == len(colonnes):
                transactions_data.append(valeurs)

print(f"  {len(transactions_data)} transactions trouvees")
print("")

# Creation des DataFrames
print("Creation des DataFrames...")

if clients_data:
    colonnes_clients = ['id', 'created_by', 'create_date_time', 'modified_by', 
                       'modified_date_time', 'first_name', 'identity', 
                       'last_name', 'phone_number', 'uuid']
    df_clients = pd.DataFrame(clients_data, columns=colonnes_clients[:len(clients_data[0])])
    print(f"  DataFrame clients: {len(df_clients)} lignes")
else:
    df_clients = pd.DataFrame()
    print("  Aucun client trouve")

if transactions_data:
    df_trans = pd.DataFrame(transactions_data, columns=colonnes)
    print(f"  DataFrame transactions: {len(df_trans)} lignes")
else:
    df_trans = pd.DataFrame()
    print("  Aucune transaction trouvee")
print("")

# Nettoyage des donnees
print("Nettoyage des donnees...")

if len(df_trans) > 0:
    df = df_trans.copy()
    
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    df = df[df['amount'] > 0]
    df = df[df['amount'] < 1000000]
    df = df.dropna(subset=['transaction_date'])
    
    df['annee'] = df['transaction_date'].dt.year
    df['mois'] = df['transaction_date'].dt.month
    df['jour'] = df['transaction_date'].dt.day
    df['jour_semaine'] = df['transaction_date'].dt.day_name()
    df['mois_annee'] = df['transaction_date'].dt.to_period('M')
    
    print(f"  Transactions apres nettoyage: {len(df)}")
    print(f"  Montant total: {df['amount'].sum():,.2f}")
    print(f"  Montant moyen: {df['amount'].mean():,.2f}")
    print(f"  Periode: {df['transaction_date'].min()} a {df['transaction_date'].max()}")
    print("")
    
    # Analyse par client
    print("Analyse par client...")
    
    if len(df_clients) > 0:
        df_avec_clients = pd.merge(
            df,
            df_clients[['id', 'phone_number', 'first_name', 'last_name']],
            left_on='client_id',
            right_on='id',
            how='left'
        )
    else:
        df_avec_clients = df.copy()
        df_avec_clients['phone_number'] = 'Inconnu'
    
    stats_clients = df_avec_clients.groupby('client_id').agg({
        'amount': ['count', 'sum', 'mean']
    }).round(2)
    
    stats_clients.columns = ['nb_transactions', 'montant_total', 'montant_moyen']
    stats_clients = stats_clients.reset_index()
    stats_clients = stats_clients[stats_clients['nb_transactions'] > 0]
    
    print(f"  Nombre de clients actifs: {len(stats_clients)}")
    print("")
    
    # Classification
    print("Classification des clients...")
    
    seuil_frequence = stats_clients['nb_transactions'].median()
    seuil_montant = stats_clients['montant_moyen'].median()
    
    print(f"  Seuils utilises:")
    print(f"    Frequence mediane: {seuil_frequence:.0f} transactions")
    print(f"    Montant moyen median: {seuil_montant:.2f}")
    
    def classifier_client(row):
        if row['nb_transactions'] >= seuil_frequence and row['montant_moyen'] >= seuil_montant:
            return "Gros depensier regulier"
        elif row['nb_transactions'] >= seuil_frequence and row['montant_moyen'] < seuil_montant:
            return "Petit depensier regulier"
        elif row['nb_transactions'] < seuil_frequence and row['montant_moyen'] >= seuil_montant:
            return "Gros depensier occasionnel"
        else:
            return "Petit depensier occasionnel"
    
    stats_clients['profil'] = stats_clients.apply(classifier_client, axis=1)
    
    print("  Distribution des profils:")
    profil_counts = stats_clients['profil'].value_counts()
    for profil, count in profil_counts.items():
        pourcentage = (count / len(stats_clients)) * 100
        print(f"    {profil}: {count} clients ({pourcentage:.1f}%)")
    print("")
    
    # Creation des graphiques
    print("Creation des graphiques...")
    
    plt.style.use('ggplot')
    fig = plt.figure(figsize=(20, 12))
    
    plt.subplot(2, 3, 1)
    evolution = df.groupby('mois_annee')['amount'].sum()
    evolution.plot(kind='line', marker='o', linewidth=2)
    plt.title('Evolution mensuelle des montants', fontsize=14)
    plt.xlabel('Mois')
    plt.ylabel('Montant total')
    plt.xticks(rotation=45)
    
    plt.subplot(2, 3, 2)
    jour_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['jour_semaine'] = pd.Categorical(df['jour_semaine'], categories=jour_order, ordered=True)
    jour_stats = df.groupby('jour_semaine')['amount'].sum()
    jour_stats.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Montants par jour de semaine', fontsize=14)
    plt.xlabel('Jour')
    plt.ylabel('Montant total')
    plt.xticks(rotation=45)
    
    plt.subplot(2, 3, 3)
    top_clients = stats_clients.nlargest(10, 'montant_total')[['client_id', 'montant_total']]
    top_clients.plot(kind='barh', x='client_id', y='montant_total', legend=False, color='coral')
    plt.title('Top 10 clients par montant total', fontsize=14)
    plt.xlabel('Montant total')
    
    plt.subplot(2, 3, 4)
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    profil_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('Repartition des profils clients', fontsize=14)
    plt.ylabel('')
    
    plt.subplot(2, 3, 5)
    plt.hist(df['amount'], bins=50, edgecolor='black', alpha=0.7, color='green')
    plt.title('Distribution des montants', fontsize=14)
    plt.xlabel('Montant')
    plt.ylabel('Frequence')
    
    plt.subplot(2, 3, 6)
    trans_par_mois = df.groupby('mois_annee').size()
    trans_par_mois.plot(kind='bar', color='purple', alpha=0.7)
    plt.title('Nombre de transactions par mois', fontsize=14)
    plt.xlabel('Mois')
    plt.ylabel('Nombre de transactions')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('analyse_complete.png', dpi=150, bbox_inches='tight')
    print("  Graphique sauvegarde: analyse_complete.png")
    print("")
    
    # Sauvegarde des resultats
    print("Sauvegarde des resultats...")
    
    df.to_csv('transactions_nettoyees.csv', index=False, encoding='utf-8')
    print("  transactions_nettoyees.csv")
    
    stats_clients.to_csv('statistiques_clients.csv', index=False, encoding='utf-8')
    print("  statistiques_clients.csv")
    
    with open('resume_etl.txt', 'w', encoding='utf-8') as f:
        f.write("RESUME ETL - SMART PERSONAL FINANCE WALLET\n\n")
        f.write(f"Date de l'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write("STATISTIQUES GLOBALES:\n")
        f.write(f"  Nombre de transactions: {len(df_trans):,}\n")
        f.write(f"  Transactions apres nettoyage: {len(df):,}\n")
        f.write(f"  Montant total: {df['amount'].sum():,.2f}\n")
        f.write(f"  Montant moyen: {df['amount'].mean():,.2f}\n\n")
        f.write("PERIODE ANALYSEE:\n")
        f.write(f"  Du: {df['transaction_date'].min()}\n")
        f.write(f"  Au: {df['transaction_date'].max()}\n\n")
        f.write("CLASSIFICATION DES CLIENTS:\n")
        for profil, count in profil_counts.items():
            pourcentage = (count / len(stats_clients)) * 100
            f.write(f"  {profil}: {count} clients ({pourcentage:.1f}%)\n")
    
    print("  resume_etl.txt")
    print("")
    
    print("ETL termine avec succes")
    print("")
    print("Fichiers generes:")
    print("  transactions_nettoyees.csv")
    print("  statistiques_clients.csv")
    print("  resume_etl.txt")
    print("  analyse_complete.png")
    
else:
    print("Aucune transaction trouvee!")