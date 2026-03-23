import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'

def creer_graphiques_profils(stats_clients, recommandations, chemin="output"):
    """
    Crée des graphiques avancés pour l'analyse des profils
    """
    if len(stats_clients) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Figure 1: Distribution des 6 profils
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse détaillée des profils clients - 6 catégories', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. Répartition des profils
    ax1 = axes[0, 0]
    profil_counts = stats_clients['profil'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(profil_counts)))
    wedges, texts, autotexts = ax1.pie(profil_counts.values, 
                                         labels=profil_counts.index,
                                         autopct='%1.1f%%',
                                         colors=colors,
                                         textprops={'fontsize': 8})
    ax1.set_title('Répartition des 6 profils clients', fontsize=12, fontweight='bold')
    
    # 2. Montant total par profil
    ax2 = axes[0, 1]
    total_par_profil = stats_clients.groupby('profil')['montant_total'].sum().sort_values(ascending=True)
    ax2.barh(total_par_profil.index, total_par_profil.values / 1_000_000, 
             color=ROSE_EXCELLIA, edgecolor='white')
    ax2.set_title('Montant total par profil (millions TND)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Montant total (millions)')
    
    # 3. Nombre moyen de transactions par profil
    ax3 = axes[1, 0]
    trans_par_profil = stats_clients.groupby('profil')['nb_transactions'].mean().sort_values()
    ax3.barh(trans_par_profil.index, trans_par_profil.values, 
             color=BLEU_EXCELLIA, edgecolor='white')
    ax3.set_title('Nombre moyen de transactions par profil', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Nombre de transactions')
    
    # 4. Montant moyen par transaction par profil
    ax4 = axes[1, 1]
    montant_moyen_par_profil = stats_clients.groupby('profil')['montant_moyen'].mean().sort_values()
    ax4.barh(montant_moyen_par_profil.index, montant_moyen_par_profil.values, 
             color=ROSE_EXCELLIA, edgecolor='white')
    ax4.set_title('Montant moyen par transaction (TND)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Montant moyen (TND)')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/profils_clients_6_categories.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Graphique profils sauvegardé: {chemin}/profils_clients_6_categories.png")
    
    # Figure 2: Matrice de segmentation
    if len(stats_clients) > 0:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Créer une matrice de segmentation (fréquence vs montant)
            freq_bins = pd.qcut(stats_clients['nb_transactions'], q=4, labels=['Faible', 'Moyen-faible', 'Moyen-élevé', 'Élevé'], duplicates='drop')
            amount_bins = pd.qcut(stats_clients['montant_moyen'], q=4, labels=['Faible', 'Moyen-faible', 'Moyen-élevé', 'Élevé'], duplicates='drop')
            
            # Compter les clients dans chaque case
            matrix = pd.crosstab(freq_bins, amount_bins)
            
            # Afficher la heatmap
            im = ax.imshow(matrix.values, cmap='Reds', aspect='auto')
            ax.set_xticks(range(len(matrix.columns)))
            ax.set_yticks(range(len(matrix.index)))
            ax.set_xticklabels(matrix.columns)
            ax.set_yticklabels(matrix.index)
            ax.set_xlabel('Montant moyen des transactions', fontsize=12, fontweight='bold')
            ax.set_ylabel('Fréquence des transactions', fontsize=12, fontweight='bold')
            ax.set_title('Matrice de segmentation clients\n(Fréquence vs Montant)', 
                         fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
            
            # Ajouter les valeurs dans chaque case
            for i in range(len(matrix.index)):
                for j in range(len(matrix.columns)):
                    text = ax.text(j, i, matrix.values[i, j],
                                 ha="center", va="center", 
                                 color="white" if matrix.values[i, j] > matrix.values.max()/2 else "black")
            
            plt.colorbar(im, label="Nombre de clients")
            plt.tight_layout()
            plt.savefig(f"{chemin}/matrice_segmentation_clients.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✅ Matrice de segmentation sauvegardée: {chemin}/matrice_segmentation_clients.png")
        except Exception as e:
            print(f"  ⚠️ Erreur matrice de segmentation: {e}")

def creer_graphiques_recommandations(recommandations, chemin="output"):
    """
    Crée des graphiques sur les recommandations par profil
    """
    if len(recommandations) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Analyse des recommandations personnalisées', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. Distribution des profils pour recommandations
    ax1 = axes[0]
    profil_counts = recommandations['profil'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(profil_counts)))
    ax1.pie(profil_counts.values, labels=profil_counts.index, autopct='%1.1f%%',
            colors=colors, textprops={'fontsize': 9})
    ax1.set_title('Clients éligibles aux recommandations', fontsize=12, fontweight='bold')
    
    # 2. Montant total par profil de recommandation
    ax2 = axes[1]
    total_par_profil = recommandations.groupby('profil')['montant_total'].sum().sort_values()
    ax2.barh(total_par_profil.index, total_par_profil.values / 1_000_000, 
             color=ROSE_EXCELLIA, edgecolor='white')
    ax2.set_title('Montant total par profil (millions TND)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Montant total (millions)')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/analyse_recommandations.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Graphique recommandations sauvegardé: {chemin}/analyse_recommandations.png")