import matplotlib.pyplot as plt
import pandas as pd

# Couleurs du logo Excellia
ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
GRIS_CLAIR = '#F5F5F5'

def creer_graphiques(df_trans, df_stats, profil_counts, chemin):
    """Cree tous les graphiques pour l'analyse"""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('Analyse des transactions - Smart Personal Finance Wallet', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. TOP 10 CLIENTS
    plt.subplot(2, 3, 1)
    top10 = df_stats.nlargest(10, 'montant_total').copy()
    top10 = top10.sort_values('montant_total', ascending=True)
    top10['client'] = ['Client ' + str(i+1) for i in range(9, -1, -1)]
    top10['montant_total_millions'] = top10['montant_total'] / 1_000_000
    
    colors = [ROSE_EXCELLIA if i < 5 else BLEU_EXCELLIA for i in range(10)]
    bars = plt.barh(top10['client'], top10['montant_total_millions'], 
                    color=colors, edgecolor='white', linewidth=1.5)
    plt.title('Top 10 clients par montant total', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant total (millions)', fontsize=11)
    plt.ylabel('Client', fontsize=11)
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}M', 
                ha='left', va='center', fontsize=9, fontweight='bold')
    
    # 2. REPARTITION DES PROFILS
    plt.subplot(2, 3, 2)
    # Récupérer les noms exacts des profils
    profils = list(profil_counts.index)
    colors_pie = [ROSE_EXCELLIA, BLEU_EXCELLIA]
    wedges, texts, autotexts = plt.pie(
        profil_counts.values, 
        labels=profils,
        autopct='%1.1f%%',
        colors=colors_pie, 
        startangle=90, 
        explode=(0.05, 0.05),
        textprops={'fontsize': 11, 'fontweight': 'bold'}
    )
    plt.setp(autotexts, size=11, weight="bold", color="white")
    plt.title('Répartition des profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 3. MONTANT MOYEN PAR PROFIL
    plt.subplot(2, 3, 3)
    df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                              on='client_id', how='left')
    moyenne_par_profil = df_avec_profil.groupby('profil')['amount'].mean().round(0)
    
    bars = plt.bar(moyenne_par_profil.index, moyenne_par_profil.values,
                   color=[ROSE_EXCELLIA, BLEU_EXCELLIA], edgecolor='white', linewidth=1.5)
    plt.title('Montant moyen par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Profil', fontsize=11)
    plt.ylabel('Montant moyen', fontsize=11)
    plt.xticks(rotation=10)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 4. DISTRIBUTION DES MONTANTS
    plt.subplot(2, 3, 4)
    n, bins, patches = plt.hist(df_trans['amount'], bins=50, edgecolor='white', 
                                alpha=0.8, log=True, color=ROSE_EXCELLIA)
    plt.title('Distribution des montants (échelle log)', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant', fontsize=11)
    plt.ylabel('Fréquence (log)', fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 5. EVOLUTION MENSUELLE
    plt.subplot(2, 3, 5)
    evolution = df_trans.groupby('mois_annee')['amount'].sum() / 1_000_000
    plt.plot(range(len(evolution)), evolution.values, 
             linewidth=2, color=BLEU_EXCELLIA, marker='o', markersize=3)
    plt.title('Évolution mensuelle des montants', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Mois', fontsize=11)
    plt.ylabel('Montant total (millions)', fontsize=11)
    plt.xticks(range(0, len(evolution), 6), 
               [str(d) for d in evolution.index[::6]], rotation=45)
    plt.grid(True, alpha=0.3)
    
    # 6. NOMBRE DE TRANSACTIONS PAR MOIS
    plt.subplot(2, 3, 6)
    trans_par_mois = df_trans.groupby('mois_annee').size()
    plt.bar(range(len(trans_par_mois)), trans_par_mois.values, 
            color=ROSE_EXCELLIA, edgecolor='white', linewidth=1, alpha=0.8)
    plt.title('Nombre de transactions par mois', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Mois', fontsize=11)
    plt.ylabel('Nombre de transactions', fontsize=11)
    plt.xticks(range(0, len(trans_par_mois), 6), 
               [str(d) for d in trans_par_mois.index[::6]], rotation=45)
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_principaux.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Graphiques sauvegardes: {chemin}/graphiques_excellia_principaux.png")
    
    # Appel de la fonction pour les graphiques détaillés
    creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin)


def creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin):
    """Cree les graphiques detailles"""
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Analyse détaillée des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. Boxplot des montants par profil
    df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                              on='client_id', how='left')
    
    # Récupérer les noms exacts des profils
    profils = list(profil_counts.index)
    profil1 = profils[0]  # Premier profil (Gros depensier regulier)
    profil2 = profils[1]  # Second profil (Petit depensier regulier)
    
    # Préparer les données pour le boxplot
    data_gros = df_avec_profil[df_avec_profil['profil'] == profil1]['amount']
    data_petit = df_avec_profil[df_avec_profil['profil'] == profil2]['amount']
    
    data_to_plot = [data_gros, data_petit]
    
    # Créer le boxplot
    bp = axes[0].boxplot(data_to_plot, labels=['Gros depensier', 'Petit depensier'],
                         patch_artist=True,
                         boxprops=dict(facecolor=ROSE_EXCELLIA, color=BLEU_EXCELLIA, alpha=0.7),
                         whiskerprops=dict(color=BLEU_EXCELLIA),
                         capprops=dict(color=BLEU_EXCELLIA),
                         medianprops=dict(color='white', linewidth=2),
                         flierprops=dict(marker='o', markerfacecolor=ROSE_EXCELLIA,
                                        markersize=4, alpha=0.5))
    
    axes[0].set_title('Distribution des montants par profil', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Profil')
    axes[0].set_ylabel('Montant')
    axes[0].set_yscale('log')
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # 2. Camembert avec détails
    wedges, texts, autotexts = axes[1].pie(
        profil_counts.values, 
        labels=[f'{profil1}\n({profil_counts[profil1]} clients)', 
                f'{profil2}\n({profil_counts[profil2]} clients)'],
        autopct='%1.1f%%',
        colors=[ROSE_EXCELLIA, BLEU_EXCELLIA], 
        startangle=90,
        explode=(0.05, 0.05),
        textprops={'fontsize': 11, 'fontweight': 'bold'}
    )
    plt.setp(autotexts, size=11, weight="bold", color="white")
    axes[1].set_title('Détail des profils clients', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_detail.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Graphiques detail sauvegardes: {chemin}/graphiques_excellia_detail.png")