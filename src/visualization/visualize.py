import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
VERT_EXCELLIA = '#2E8B57'
ORANGE_EXCELLIA = '#FF8C00'

# Configuration pour éviter les problèmes d'affichage
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['svg.fonttype'] = 'none'


def creer_graphiques(df_transactions, stats_clients, profil_counts, chemin="output"):
    """
    Crée 4 graphiques de visualisation avec les données réelles
    """
    if len(df_transactions) == 0:
        print("Données insuffisantes pour les graphiques")
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # =========================================================
    # GRAPHIQUE 1: Top 10 clients par montant total
    # =========================================================
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    
    top10 = stats_clients.nlargest(10, 'montant_total')
    
    client_labels = [f'Client #{i+1}' for i in range(len(top10))]
    montants = top10['montant_total'].values
    
    bars = ax1.bar(range(len(top10)), montants, color=ROSE_EXCELLIA, edgecolor='white', linewidth=1.5)
    
    ax1.set_title('Top 10 des clients par montant total dépensé', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    ax1.set_xlabel('Client', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Montant total dépensé (TND)', fontsize=11, fontweight='bold')
    ax1.set_xticks(range(len(top10)))
    ax1.set_xticklabels(client_labels, rotation=45, ha='right')
    
    for bar, val in zip(bars, montants):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(montants)*0.01,
                f'{val:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(f"{chemin}/01_top10_clients_montant.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Graphique 1/4: top10_clients_montant.png")
    
    # =========================================================
    # GRAPHIQUE 2: Répartition des 4 profils clients (camembert propre)
    # =========================================================
    fig2, ax2 = plt.subplots(figsize=(9, 7))
    
    # Nettoyer et préparer les données
    profil_data = {}
    ordre_profils = ['Premium', 'Gros dépensier actif', 'Client régulier', 'Client occasionnel']
    
    for profil in ordre_profils:
        if profil in profil_counts.index:
            profil_data[profil] = profil_counts[profil]
        else:
            profil_data[profil] = 0
    
    # Enlever les profils avec 0
    labels = [p for p in ordre_profils if profil_data[p] > 0]
    values = [profil_data[p] for p in labels]
    
    colors = [ROSE_EXCELLIA, ORANGE_EXCELLIA, BLEU_EXCELLIA, VERT_EXCELLIA][:len(labels)]
    
    # Création du camembert
    wedges, texts, autotexts = ax2.pie(values, 
                                        labels=labels,
                                        autopct=lambda pct: f'{pct:.1f}%',
                                        colors=colors,
                                        explode=[0.03] * len(labels),
                                        shadow=True,
                                        startangle=90,
                                        textprops={'fontsize': 11})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
    
    ax2.set_title('Répartition des profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/02_repartition_profils_clients.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Graphique 2/4: repartition_profils_clients.png")
    
    # =========================================================
    # GRAPHIQUE 3: Distribution des montants (filtrer les outliers)
    # =========================================================
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    
    amounts = df_transactions['amount'].values
    
    # Filtrer les valeurs aberrantes pour meilleure visualisation
    q95 = np.percentile(amounts, 95)
    amounts_filtered = amounts[amounts <= q95]
    
    print(f"   Distribution: {len(amounts_filtered)} transactions sur {len(amounts)} (filtre 95e percentile)")
    
    # Histogramme
    n, bins, patches = ax3.hist(amounts_filtered, bins=40, color=BLEU_EXCELLIA, alpha=0.7, edgecolor='white', linewidth=1)
    
    # Statistiques réelles
    mean_val = amounts.mean()
    median_val = np.median(amounts)
    
    ax3.axvline(mean_val, color=ROSE_EXCELLIA, linestyle='dashed', linewidth=2.5, 
                label=f'Moyenne: {mean_val:,.0f} TND')
    ax3.axvline(median_val, color=VERT_EXCELLIA, linestyle='dashed', linewidth=2.5, 
                label=f'Médiane: {median_val:,.0f} TND')
    
    ax3.set_title('Distribution des montants de transaction', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    ax3.set_xlabel('Montant (TND)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Nombre de transactions', fontsize=11, fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Statistiques résumées
    stats_text = f"Total: {len(amounts):,} transactions\nMin: {amounts.min():,.0f} TND\nMax: {amounts.max():,.0f} TND"
    ax3.text(0.98, 0.95, stats_text, transform=ax3.transAxes, fontsize=9,
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/03_distribution_montants_transactions.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Graphique 3/4: distribution_montants_transactions.png")
    
    # =========================================================
    # GRAPHIQUE 4: Évolution mensuelle (agrégée par mois)
    # =========================================================
    if 'mois_annee' in df_transactions.columns:
        fig4, ax4 = plt.subplots(figsize=(14, 6))
        
        # Agrégation par mois
        monthly_amount = df_transactions.groupby('mois_annee')['amount'].sum()
        
        # Convertir en string pour l'affichage
        months = [str(m) for m in monthly_amount.index]
        
        # Afficher tous les 3 mois pour lisibilité
        step = max(1, len(months) // 10)
        xticks_pos = range(0, len(months), step)
        xticks_labels = [months[i] for i in xticks_pos]
        
        ax4.plot(range(len(months)), monthly_amount.values, color=ROSE_EXCELLIA, marker='o', 
                linewidth=2, markersize=6)
        ax4.fill_between(range(len(months)), monthly_amount.values, alpha=0.3, color=ROSE_EXCELLIA)
        
        ax4.set_title('Évolution mensuelle du volume des transactions', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        ax4.set_xlabel('Mois', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Montant total (TND)', fontsize=11, fontweight='bold')
        ax4.set_xticks(xticks_pos)
        ax4.set_xticklabels(xticks_labels, rotation=45, ha='right')
        ax4.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(f"{chemin}/04_evolution_mensuelle_transactions.png", dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Graphique 4/4: evolution_mensuelle_transactions.png")
    
    print(f"\n Graphiques générés dans '{chemin}/'")


def creer_graphiques_profils_avances(stats_clients, recommendations, chemin="output"):
    """Graphique d'analyse avancée des profils"""
    if len(stats_clients) == 0:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Graphique 1: Montant total par profil
    total_par_profil = stats_clients.groupby('profil')['montant_total'].sum()
    # Réordonner
    ordre = ['Premium', 'Gros dépensier actif', 'Client régulier', 'Client occasionnel']
    total_par_profil = total_par_profil.reindex([p for p in ordre if p in total_par_profil.index])
    
    bars1 = axes[0].bar(total_par_profil.index, total_par_profil.values, color=ROSE_EXCELLIA, edgecolor='white')
    axes[0].set_title('Montant total par profil', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Montant total (TND)', fontsize=10)
    axes[0].tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars1, total_par_profil.values):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val/1000:.1f}K', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Graphique 2: Nombre moyen de transactions par profil
    trans_par_profil = stats_clients.groupby('profil')['nb_transactions'].mean()
    trans_par_profil = trans_par_profil.reindex([p for p in ordre if p in trans_par_profil.index])
    
    bars2 = axes[1].bar(trans_par_profil.index, trans_par_profil.values, color=BLEU_EXCELLIA, edgecolor='white')
    axes[1].set_title('Nombre moyen de transactions par profil', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Nombre de transactions', fontsize=10)
    axes[1].tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars2, trans_par_profil.values):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.suptitle('Analyse comparative des profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.tight_layout()
    plt.savefig(f"{chemin}/05_analyse_profils_avancee.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Graphique bonus: analyse_profils_avancee.png")