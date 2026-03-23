import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Couleurs du logo Excellia
ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
GRIS_CLAIR = '#F5F5F5'

def creer_graphiques(df_trans, df_stats, profil_counts, chemin):
    """Cree tous les graphiques pour l'analyse (supporte 2 ou 6 profils)"""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('Analyse des transactions - Smart Personal Finance Wallet', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. TOP 10 CLIENTS
    plt.subplot(2, 3, 1)
    top10 = df_stats.nlargest(10, 'montant_total').copy()
    top10 = top10.sort_values('montant_total', ascending=True)
    top10['client'] = ['Client ' + str(i+1) for i in range(len(top10)-1, -1, -1)]
    top10['montant_total_millions'] = top10['montant_total'] / 1_000_000
    
    colors = [ROSE_EXCELLIA if i < 5 else BLEU_EXCELLIA for i in range(len(top10))]
    bars = plt.barh(top10['client'], top10['montant_total_millions'], 
                    color=colors, edgecolor='white', linewidth=1.5)
    plt.title('Top 10 clients par montant total', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant total (millions)', fontsize=11)
    plt.ylabel('Client', fontsize=11)
    
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}M', 
                    ha='left', va='center', fontsize=9, fontweight='bold')
    
    # 2. REPARTITION DES PROFILS (adapté au nombre de profils)
    plt.subplot(2, 3, 2)
    
    # Créer une palette de couleurs en fonction du nombre de profils
    n_profils = len(profil_counts)
    if n_profils <= 2:
        colors_pie = [ROSE_EXCELLIA, BLEU_EXCELLIA]
    elif n_profils <= 4:
        colors_pie = [ROSE_EXCELLIA, BLEU_EXCELLIA, '#FFA500', '#4CAF50']
    else:
        # Pour 6 profils, utiliser une palette dégradée
        colors_pie = plt.cm.Set3(np.linspace(0, 1, n_profils))
    
    # Ajuster l'explosion pour les petits secteurs
    explode = tuple([0.02] * n_profils) if n_profils > 2 else (0.05, 0.05)
    
    wedges, texts, autotexts = plt.pie(
        profil_counts.values, 
        labels=profil_counts.index,
        autopct='%1.1f%%',
        colors=colors_pie[:n_profils], 
        startangle=90, 
        explode=explode,
        textprops={'fontsize': 10, 'fontweight': 'bold'}
    )
    
    # Ajuster la taille des textes selon le nombre de profils
    if n_profils > 4:
        for text in texts:
            text.set_fontsize(8)
    
    if autotexts:
        plt.setp(autotexts, size=9, weight="bold")
    
    plt.title(f'Répartition des {n_profils} profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 3. MONTANT MOYEN PAR PROFIL
    plt.subplot(2, 3, 3)
    
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        moyenne_par_profil = df_avec_profil.groupby('profil')['amount'].mean().round(0)
        
        # Créer une palette pour les barres
        bar_colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(moyenne_par_profil))]
        
        bars = plt.bar(range(len(moyenne_par_profil)), moyenne_par_profil.values,
                       color=bar_colors[:len(moyenne_par_profil)], edgecolor='white', linewidth=1.5)
        plt.title('Montant moyen par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        plt.xlabel('Profil', fontsize=11)
        plt.ylabel('Montant moyen (TND)', fontsize=11)
        plt.xticks(range(len(moyenne_par_profil)), moyenne_par_profil.index, rotation=15, ha='right')
        
        for bar, val in zip(bars, moyenne_par_profil.values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 4. DISTRIBUTION DES MONTANTS
    plt.subplot(2, 3, 4)
    n, bins, patches = plt.hist(df_trans['amount'], bins=50, edgecolor='white', 
                                alpha=0.8, log=True, color=ROSE_EXCELLIA)
    
    # Colorer les barres avec un dégradé
    for i, patch in enumerate(patches):
        patch.set_facecolor(ROSE_EXCELLIA)
        patch.set_alpha(0.7)
    
    plt.title('Distribution des montants (échelle log)', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant (TND)', fontsize=11)
    plt.ylabel('Fréquence (log)', fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 5. EVOLUTION MENSUELLE
    plt.subplot(2, 3, 5)
    if 'mois_annee' in df_trans.columns:
        evolution = df_trans.groupby('mois_annee')['amount'].sum() / 1_000_000
        if len(evolution) > 0:
            plt.plot(range(len(evolution)), evolution.values, 
                     linewidth=2, color=BLEU_EXCELLIA, marker='o', markersize=4)
            plt.fill_between(range(len(evolution)), evolution.values, alpha=0.2, color=BLEU_EXCELLIA)
            plt.title('Évolution mensuelle des montants', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
            plt.xlabel('Mois', fontsize=11)
            plt.ylabel('Montant total (millions TND)', fontsize=11)
            
            # Ajuster les ticks pour éviter le chevauchement
            step = max(1, len(evolution) // 6)
            plt.xticks(range(0, len(evolution), step), 
                       [str(d) for d in evolution.index[::step]], rotation=45)
            plt.grid(True, alpha=0.3)
    
    # 6. NOMBRE DE TRANSACTIONS PAR MOIS
    plt.subplot(2, 3, 6)
    if 'mois_annee' in df_trans.columns:
        trans_par_mois = df_trans.groupby('mois_annee').size()
        if len(trans_par_mois) > 0:
            plt.bar(range(len(trans_par_mois)), trans_par_mois.values, 
                    color=ROSE_EXCELLIA, edgecolor='white', linewidth=1, alpha=0.8)
            plt.title('Nombre de transactions par mois', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
            plt.xlabel('Mois', fontsize=11)
            plt.ylabel('Nombre de transactions', fontsize=11)
            
            step = max(1, len(trans_par_mois) // 6)
            plt.xticks(range(0, len(trans_par_mois), step), 
                       [str(d) for d in trans_par_mois.index[::step]], rotation=45)
            plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_principaux.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphiques principaux sauvegardés: {chemin}/graphiques_excellia_principaux.png")
    
    # Appel de la fonction pour les graphiques détaillés
    creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin)


def creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin):
    """Cree les graphiques detailles (supporte 2 ou 6 profils)"""
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Analyse détaillée des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    n_profils = len(profil_counts)
    
    # 1. Boxplot des montants par profil
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        
        # Pour le boxplot, on limite aux 2 premiers profils si plus de 2 (lisibilité)
        if n_profils > 2:
            profils_affiches = list(profil_counts.index)[:2]
            labels = [p[:20] + '...' if len(p) > 20 else p for p in profils_affiches]  # Tronquer les noms longs
        else:
            profils_affiches = list(profil_counts.index)
            labels = profils_affiches
        
        data_to_plot = []
        for profil in profils_affiches:
            data = df_avec_profil[df_avec_profil['profil'] == profil]['amount']
            if len(data) > 0:
                data_to_plot.append(data)
        
        if data_to_plot:
            bp = axes[0].boxplot(data_to_plot, labels=labels,
                                 patch_artist=True,
                                 boxprops=dict(facecolor=ROSE_EXCELLIA, color=BLEU_EXCELLIA, alpha=0.7),
                                 whiskerprops=dict(color=BLEU_EXCELLIA),
                                 capprops=dict(color=BLEU_EXCELLIA),
                                 medianprops=dict(color='white', linewidth=2),
                                 flierprops=dict(marker='o', markerfacecolor=ROSE_EXCELLIA,
                                                markersize=4, alpha=0.5))
            
            axes[0].set_title('Distribution des montants par profil', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Profil', fontsize=11)
            axes[0].set_ylabel('Montant (TND)', fontsize=11)
            axes[0].set_yscale('log')
            axes[0].grid(True, alpha=0.3, axis='y')
            
            # Ajouter des statistiques
            for i, data in enumerate(data_to_plot):
                median = data.median()
                axes[0].text(i + 1, median * 1.1, f'méd: {median:.0f}', 
                            ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # 2. Graphique en anneau ou camembert selon le nombre de profils
    if n_profils <= 4:
        # Camembert simple
        colors_pie = [ROSE_EXCELLIA, BLEU_EXCELLIA, '#FFA500', '#4CAF50'][:n_profils]
        
        # Créer des labels avec le nombre de clients
        labels = [f'{p}\n({profil_counts[p]} clients)' for p in profil_counts.index]
        
        wedges, texts, autotexts = axes[1].pie(
            profil_counts.values, 
            labels=labels,
            autopct='%1.1f%%',
            colors=colors_pie, 
            startangle=90,
            explode=tuple([0.03] * n_profils),
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )
        
        if autotexts:
            plt.setp(autotexts, size=10, weight="bold", color="white")
        
        axes[1].set_title('Détail des profils clients', fontsize=14, fontweight='bold')
        
    else:
        # Pour 5-6 profils, utiliser un graphique en anneau (donut)
        colors_pie = plt.cm.Set3(np.linspace(0, 1, n_profils))
        
        wedges, texts, autotexts = axes[1].pie(
            profil_counts.values,
            labels=profil_counts.index,
            autopct='%1.1f%%',
            colors=colors_pie,
            startangle=90,
            pctdistance=0.85,
            textprops={'fontsize': 9}
        )
        
        # Ajouter un cercle blanc au centre pour faire un donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='white', linewidth=0)
        axes[1].add_artist(centre_circle)
        
        # Ajouter le total au centre
        axes[1].text(0, 0, f'Total\n{sum(profil_counts.values)}', 
                    ha='center', va='center', fontsize=12, fontweight='bold')
        
        axes[1].set_title(f'Répartition des {n_profils} profils', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_detail.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphiques détail sauvegardés: {chemin}/graphiques_excellia_detail.png")
    
    # Si plus de 2 profils, créer un graphique supplémentaire pour visualiser tous les profils
    if n_profils > 2:
        creer_graphique_tous_profils(df_trans, df_stats, profil_counts, chemin)


def creer_graphique_tous_profils(df_trans, df_stats, profil_counts, chemin):
    """Cree un graphique supplémentaire pour visualiser tous les profils"""
    
    if 'profil' not in df_stats.columns:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse complète des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    n_profils = len(profil_counts)
    df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                              on='client_id', how='left')
    
    # 1. Nombre de clients par profil (barres horizontales)
    ax1 = axes[0, 0]
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(profil_counts_sorted))]
    ax1.barh(profil_counts_sorted.index, profil_counts_sorted.values, color=colors, edgecolor='white')
    ax1.set_title('Nombre de clients par profil', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Nombre de clients')
    
    # Ajouter les valeurs
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        ax1.text(count + 1, i, str(count), va='center', fontsize=9)
    
    # 2. Montant total par profil
    ax2 = axes[0, 1]
    total_par_profil = df_stats.groupby('profil')['montant_total'].sum().sort_values()
    colors = [BLEU_EXCELLIA if i % 2 == 0 else ROSE_EXCELLIA for i in range(len(total_par_profil))]
    ax2.barh(total_par_profil.index, total_par_profil.values / 1_000_000, color=colors, edgecolor='white')
    ax2.set_title('Montant total par profil (millions TND)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Montant total (millions)')
    
    # 3. Fréquence moyenne par profil
    ax3 = axes[1, 0]
    freq_par_profil = df_stats.groupby('profil')['nb_transactions'].mean().sort_values()
    ax3.bar(freq_par_profil.index, freq_par_profil.values, color=ROSE_EXCELLIA, edgecolor='white')
    ax3.set_title('Nombre moyen de transactions par profil', fontsize=12, fontweight='bold')
    ax3.set_xticklabels(freq_par_profil.index, rotation=45, ha='right')
    ax3.set_ylabel('Nombre de transactions')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for i, (profil, val) in enumerate(freq_par_profil.items()):
        ax3.text(i, val + 0.5, f'{val:.0f}', ha='center', fontsize=9)
    
    # 4. Montant moyen par transaction par profil
    ax4 = axes[1, 1]
    montant_moyen_par_profil = df_stats.groupby('profil')['montant_moyen'].mean().sort_values()
    ax4.bar(montant_moyen_par_profil.index, montant_moyen_par_profil.values, color=BLEU_EXCELLIA, edgecolor='white')
    ax4.set_title('Montant moyen par transaction (TND)', fontsize=12, fontweight='bold')
    ax4.set_xticklabels(montant_moyen_par_profil.index, rotation=45, ha='right')
    ax4.set_ylabel('Montant moyen (TND)')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for i, (profil, val) in enumerate(montant_moyen_par_profil.items()):
        ax4.text(i, val + 5, f'{val:.0f}', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_tous_profils.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphique tous profils sauvegardé: {chemin}/graphiques_tous_profils.png")


def creer_graphiques_profils_avances(stats_clients, recommandations=None, chemin="output"):
    """
    Crée des graphiques avancés pour l'analyse des profils avec recommandations
    """
    if len(stats_clients) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Figure: Analyse des recommandations par type
    if recommandations is not None and len(recommandations) > 0:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('Analyse des recommandations personnalisées', 
                     fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        
        # 1. Distribution par type de recommandation
        ax1 = axes[0]
        if 'recommandation_type' in recommandations.columns:
            type_counts = recommandations['recommandation_type'].value_counts()
            colors = [ROSE_EXCELLIA, BLEU_EXCELLIA, '#FFA500', '#4CAF50']
            ax1.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%',
                    colors=colors[:len(type_counts)], startangle=90)
            ax1.set_title('Type de recommandations', fontsize=12, fontweight='bold')
        
        # 2. Montant total par type de recommandation
        ax2 = axes[1]
        if 'recommandation_type' in recommandations.columns:
            total_par_type = recommandations.groupby('recommandation_type')['montant_total'].sum()
            total_par_type = total_par_type.sort_values()
            ax2.barh(total_par_type.index, total_par_type.values / 1_000_000, 
                     color=ROSE_EXCELLIA, edgecolor='white')
            ax2.set_title('Montant total par type (millions TND)', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Montant total (millions)')
        
        # 3. Nombre de clients par type de recommandation
        ax3 = axes[2]
        if 'recommandation_type' in recommandations.columns:
            clients_par_type = recommandations.groupby('recommandation_type').size().sort_values()
            ax3.barh(clients_par_type.index, clients_par_type.values, 
                     color=BLEU_EXCELLIA, edgecolor='white')
            ax3.set_title('Nombre de clients par type', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Nombre de clients')
        
        plt.tight_layout()
        plt.savefig(f"{chemin}/analyse_recommandations_type.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ Graphique recommandations sauvegardé: {chemin}/analyse_recommandations_type.png")