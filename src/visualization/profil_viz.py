# profil_viz.py - VERSION CORRIGÉE
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
VERT_EXCELLIA = '#2E8B57'
ORANGE_EXCELLIA = '#FF8C00'

def creer_graphiques_profils(stats_clients, recommandations=None, chemin="output"):
    """
    Crée des graphiques détaillés d'analyse des profils clients
    Version corrigée avec 4 profils et style amélioré
    """
    if len(stats_clients) == 0:
        print("Aucune donnée client pour les graphiques de profils")
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse détaillée des profils clients', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA, y=1.02)
    
    # =========================================================
    # Graphique 1: Répartition des profils (Camembert amélioré)
    # =========================================================
    ax1 = axes[0, 0]
    profil_counts = stats_clients['profil'].value_counts()
    
    # S'assurer que les profils sont dans l'ordre souhaité
    ordre_profils = ['Premium', 'Gros dépensier actif', 'Client régulier', 'Client occasionnel']
    profil_counts = profil_counts.reindex([p for p in ordre_profils if p in profil_counts.index])
    
    colors = [ROSE_EXCELLIA, ORANGE_EXCELLIA, BLEU_EXCELLIA, VERT_EXCELLIA][:len(profil_counts)]
    explode = [0.03] * len(profil_counts)
    
    wedges, texts, autotexts = ax1.pie(profil_counts.values, 
                                        labels=profil_counts.index,
                                        autopct=lambda pct: f'{pct:.1f}%',
                                        colors=colors,
                                        explode=explode,
                                        shadow=True,
                                        startangle=90)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    for text in texts:
        text.set_fontweight('bold')
        text.set_fontsize(10)
    
    ax1.set_title('Répartition des profils clients', fontsize=13, fontweight='bold', color=BLEU_EXCELLIA)
    
    # =========================================================
    # Graphique 2: Montant total par profil (barres horizontales)
    # =========================================================
    ax2 = axes[0, 1]
    total_par_profil = stats_clients.groupby('profil')['montant_total'].sum().sort_values(ascending=True)
    
    # Réordonner
    total_par_profil = total_par_profil.reindex([p for p in ordre_profils if p in total_par_profil.index])
    
    bars = ax2.barh(total_par_profil.index, total_par_profil.values, 
                    color=ROSE_EXCELLIA, edgecolor='white', height=0.6)
    ax2.set_title('Montant total par profil (TND)', fontsize=13, fontweight='bold', color=BLEU_EXCELLIA)
    ax2.set_xlabel('Montant total (TND)', fontsize=11, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3, linestyle='--')
    
    max_val = total_par_profil.values.max()
    for i, (profil, val) in enumerate(total_par_profil.items()):
        if val >= 1_000_000:
            label = f'{val/1_000_000:.2f}M TND'
        elif val >= 1_000:
            label = f'{val/1_000:.1f}K TND'
        else:
            label = f'{val:.0f} TND'
        ax2.text(val + max_val * 0.02, i, label, va='center', fontsize=9, fontweight='bold')
    
    # =========================================================
    # Graphique 3: Nombre moyen de transactions par profil
    # =========================================================
    ax3 = axes[1, 0]
    trans_par_profil = stats_clients.groupby('profil')['nb_transactions'].mean().sort_values(ascending=True)
    trans_par_profil = trans_par_profil.reindex([p for p in ordre_profils if p in trans_par_profil.index])
    
    bars = ax3.barh(trans_par_profil.index, trans_par_profil.values, 
                    color=BLEU_EXCELLIA, edgecolor='white', height=0.6)
    ax3.set_title('Nombre moyen de transactions par profil', fontsize=13, fontweight='bold', color=BLEU_EXCELLIA)
    ax3.set_xlabel('Nombre de transactions', fontsize=11, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3, linestyle='--')
    
    max_trans = trans_par_profil.values.max()
    for i, (profil, val) in enumerate(trans_par_profil.items()):
        ax3.text(val + max_trans * 0.02, i, f'{val:.1f}', va='center', fontsize=9, fontweight='bold')
    
    # =========================================================
    # Graphique 4: Montant moyen par transaction
    # =========================================================
    ax4 = axes[1, 1]
    montant_moyen_par_profil = stats_clients.groupby('profil')['montant_moyen'].mean().sort_values(ascending=True)
    montant_moyen_par_profil = montant_moyen_par_profil.reindex([p for p in ordre_profils if p in montant_moyen_par_profil.index])
    
    bars = ax4.barh(montant_moyen_par_profil.index, montant_moyen_par_profil.values, 
                    color=ROSE_EXCELLIA, edgecolor='white', height=0.6)
    ax4.set_title('Montant moyen par transaction (TND)', fontsize=13, fontweight='bold', color=BLEU_EXCELLIA)
    ax4.set_xlabel('Montant moyen (TND)', fontsize=11, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3, linestyle='--')
    
    max_moyen = montant_moyen_par_profil.values.max()
    for i, (profil, val) in enumerate(montant_moyen_par_profil.items()):
        ax4.text(val + max_moyen * 0.02, i, f'{val:.0f} TND', va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/profils_clients_detail.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Graphique profils sauvegardé: {chemin}/profils_clients_detail.png")