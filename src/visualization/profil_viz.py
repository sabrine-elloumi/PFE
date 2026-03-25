import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'

def creer_graphiques_profils(stats_clients, recommandations, chemin="output"):
    if len(stats_clients) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse detaillee des profils clients', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    ax1 = axes[0, 0]
    profil_counts = stats_clients['profil'].value_counts()
    colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(profil_counts))]
    ax1.pie(profil_counts.values, labels=profil_counts.index,
            autopct='%1.1f%%', colors=colors, textprops={'fontsize': 8, 'fontweight': 'bold'})
    ax1.set_title('Repartition des profils clients', fontsize=12, fontweight='bold', color=BLEU_EXCELLIA)
    
    ax2 = axes[0, 1]
    total_par_profil = stats_clients.groupby('profil')['montant_total'].sum().sort_values(ascending=True)
    
    ax2.barh(total_par_profil.index, total_par_profil.values, 
             color=ROSE_EXCELLIA, edgecolor='white')
    ax2.set_title('Montant total par profil (TND)', fontsize=12, fontweight='bold', color=BLEU_EXCELLIA)
    ax2.set_xlabel('Montant total (TND)', fontsize=10)
    
    max_val = total_par_profil.values.max()
    for i, (profil, val) in enumerate(total_par_profil.items()):
        if val >= 1000000:
            label = f'{val/1000000:.2f}M'
        elif val >= 1000:
            label = f'{val/1000:.1f}K'
        else:
            label = f'{val:.0f}'
        ax2.text(val + max_val * 0.02, i, label, va='center', fontsize=8, fontweight='bold')
    
    ax3 = axes[1, 0]
    trans_par_profil = stats_clients.groupby('profil')['nb_transactions'].mean().sort_values()
    ax3.barh(trans_par_profil.index, trans_par_profil.values, 
             color=BLEU_EXCELLIA, edgecolor='white')
    ax3.set_title('Nombre moyen de transactions par profil', fontsize=12, fontweight='bold', color=BLEU_EXCELLIA)
    ax3.set_xlabel('Nombre de transactions', fontsize=10)
    
    max_trans = trans_par_profil.values.max()
    for i, (profil, val) in enumerate(trans_par_profil.items()):
        ax3.text(val + max_trans * 0.02, i, f'{val:.1f}', va='center', fontsize=8, fontweight='bold')
    
    ax4 = axes[1, 1]
    montant_moyen_par_profil = stats_clients.groupby('profil')['montant_moyen'].mean().sort_values()
    ax4.barh(montant_moyen_par_profil.index, montant_moyen_par_profil.values, 
             color=ROSE_EXCELLIA, edgecolor='white')
    ax4.set_title('Montant moyen par transaction (TND)', fontsize=12, fontweight='bold', color=BLEU_EXCELLIA)
    ax4.set_xlabel('Montant moyen (TND)', fontsize=10)
    
    max_moyen = montant_moyen_par_profil.values.max()
    for i, (profil, val) in enumerate(montant_moyen_par_profil.items()):
        ax4.text(val + max_moyen * 0.02, i, f'{val:.0f}', va='center', fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/profils_clients_detail.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Graphique profils sauvegarde: {chemin}/profils_clients_detail.png")