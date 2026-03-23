import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Couleurs du logo Excellia
ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
GRIS_CLAIR = '#F5F5F5'

# Palette de couleurs personnalisées pour les types de recommandations
TYPE_COLORS = {
    'premium': '#FFD700',      # Or
    'fidelisation': '#E6007E', # Rose Excellia
    'engagement': '#FF6B6B',   # Rouge corail (plus visible)
    'education': '#4ECDC4',    # Turquoise
    'standard': '#95A5A6',     # Gris
    'acquisition': '#2ECC71'   # Vert
}

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
    
    # 2. REPARTITION DES PROFILS (version barres horizontales pour meilleure lisibilité)
    plt.subplot(2, 3, 2)
    
    n_profils = len(profil_counts)
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    colors_bar = plt.cm.Set3(np.linspace(0, 1, n_profils))
    
    bars = plt.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values,
                    color=colors_bar, edgecolor='white', linewidth=1.5)
    plt.yticks(range(len(profil_counts_sorted)), profil_counts_sorted.index, fontsize=9)
    plt.title(f'Répartition des {n_profils} profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Nombre de clients', fontsize=11)
    
    total_clients = sum(profil_counts_sorted.values)
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        plt.text(count + total_clients * 0.01, i, f'{count} ({percentage:.1f}%)', 
                va='center', fontsize=8, fontweight='bold')
    
    # 3. MONTANT MOYEN PAR PROFIL
    plt.subplot(2, 3, 3)
    
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        moyenne_par_profil = df_avec_profil.groupby('profil')['amount'].mean().round(0)
        
        # Limiter aux 6 premiers pour lisibilité
        if len(moyenne_par_profil) > 6:
            moyenne_par_profil = moyenne_par_profil.nlargest(6)
        
        bar_colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(moyenne_par_profil))]
        
        bars = plt.bar(range(len(moyenne_par_profil)), moyenne_par_profil.values,
                       color=bar_colors, edgecolor='white', linewidth=1.5)
        plt.title('Montant moyen par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        plt.xlabel('Profil', fontsize=11)
        plt.ylabel('Montant moyen (TND)', fontsize=11)
        plt.xticks(range(len(moyenne_par_profil)), moyenne_par_profil.index, rotation=15, ha='right', fontsize=8)
        
        for bar, val in zip(bars, moyenne_par_profil.values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 4. DISTRIBUTION DES MONTANTS
    plt.subplot(2, 3, 4)
    n, bins, patches = plt.hist(df_trans['amount'], bins=50, edgecolor='white', 
                                alpha=0.8, log=True, color=ROSE_EXCELLIA)
    
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
    """Cree les graphiques detailles avec meilleure lisibilité"""
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Analyse détaillée des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    n_profils = len(profil_counts)
    
    # 1. Boxplot des montants par profil (limité aux 5 premiers pour lisibilité)
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        
        # Prendre les 5 profils les plus représentés pour le boxplot
        top_profils = profil_counts.nlargest(5).index.tolist()
        
        data_to_plot = []
        labels = []
        for profil in top_profils:
            data = df_avec_profil[df_avec_profil['profil'] == profil]['amount']
            if len(data) > 0:
                data_to_plot.append(data)
                # Tronquer les noms longs
                short_name = profil[:25] + '...' if len(profil) > 25 else profil
                labels.append(short_name)
        
        if data_to_plot:
            # Palette de couleurs pour les boxplots
            box_colors = [ROSE_EXCELLIA, BLEU_EXCELLIA, '#FFA500', '#4CAF50', '#9C27B0']
            
            bp = axes[0].boxplot(data_to_plot, labels=labels,
                                 patch_artist=True,
                                 boxprops=dict(facecolor=ROSE_EXCELLIA, color=BLEU_EXCELLIA, alpha=0.7),
                                 whiskerprops=dict(color=BLEU_EXCELLIA),
                                 capprops=dict(color=BLEU_EXCELLIA),
                                 medianprops=dict(color='white', linewidth=2),
                                 flierprops=dict(marker='o', markerfacecolor=ROSE_EXCELLIA,
                                                markersize=4, alpha=0.5))
            
            # Colorer chaque boîte différemment
            for i, patch in enumerate(bp['boxes']):
                patch.set_facecolor(box_colors[i % len(box_colors)])
                patch.set_alpha(0.7)
            
            axes[0].set_title('Distribution des montants par profil (Top 5)', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Profil', fontsize=11)
            axes[0].set_ylabel('Montant (TND)', fontsize=11)
            axes[0].set_yscale('log')
            axes[0].grid(True, alpha=0.3, axis='y')
            plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=15, ha='right', fontsize=9)
    
    # 2. Graphique en barres horizontales pour la répartition des profils (plus lisible)
    ax2 = axes[1]
    
    # Trier par nombre de clients décroissant
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    
    # Créer une palette de couleurs pour chaque profil
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(profil_counts_sorted)))
    
    # Barres horizontales avec étiquettes claires
    bars = ax2.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values, 
                    color=colors_pie, edgecolor='white', linewidth=1.5, height=0.7)
    
    # Ajouter les étiquettes
    ax2.set_yticks(range(len(profil_counts_sorted)))
    ax2.set_yticklabels(profil_counts_sorted.index, fontsize=9)
    ax2.set_xlabel('Nombre de clients', fontsize=12, fontweight='bold')
    ax2.set_title('Répartition des clients par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    # Ajouter les valeurs et pourcentages à côté des barres
    total_clients = sum(profil_counts_sorted.values)
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        ax2.text(count + total_clients * 0.01, i, 
                f'{count} clients ({percentage:.1f}%)', 
                va='center', fontsize=9, fontweight='bold')
    
    # Ajouter une grille légère
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_detail.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphiques détail sauvegardés: {chemin}/graphiques_excellia_detail.png")
    
    # Créer un graphique circulaire séparé pour la répartition
    creer_graphique_circulaire_profils(profil_counts, chemin)
    creer_graphique_barres_profils(profil_counts, chemin)


def creer_graphique_circulaire_profils(profil_counts, chemin):
    """Crée un graphique circulaire clair et bien organisé"""
    
    plt.figure(figsize=(14, 12))
    
    n_profils = len(profil_counts)
    total_clients = sum(profil_counts.values)
    
    # Trier par nombre de clients décroissant pour meilleure lisibilité
    profil_counts_sorted = profil_counts.sort_values(ascending=False)
    
    # Créer une palette de couleurs distinctes
    colors = plt.cm.Set3(np.linspace(0, 1, n_profils))
    
    # Créer des labels avec les pourcentages et retours à la ligne
    labels = []
    for profil, count in profil_counts_sorted.items():
        percentage = (count / total_clients) * 100
        # Formater le nom du profil avec retour à la ligne si trop long
        if len(profil) > 30:
            # Couper le nom en plusieurs lignes
            words = profil.split()
            if len(words) > 3:
                lines = []
                current_line = []
                char_count = 0
                for word in words:
                    if char_count + len(word) < 28:
                        current_line.append(word)
                        char_count += len(word) + 1
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                        char_count = len(word) + 1
                if current_line:
                    lines.append(' '.join(current_line))
                label_text = '\n'.join(lines)
            else:
                label_text = profil
        else:
            label_text = profil
        
        labels.append(f'{label_text}\n({count} clients, {percentage:.1f}%)')
    
    # Créer le camembert
    wedges, texts, autotexts = plt.pie(
        profil_counts_sorted.values,
        labels=labels,
        autopct='',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 9, 'fontweight': 'normal'},
        pctdistance=0.85
    )
    
    # Ajouter un titre clair
    plt.title(f'Répartition des {n_profils} profils clients\nTotal: {total_clients} clients', 
              fontsize=16, fontweight='bold', color=BLEU_EXCELLIA, pad=20)
    
    # Ajuster pour une meilleure lisibilité
    plt.tight_layout()
    plt.savefig(f"{chemin}/repartition_profils_circulaire.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphique circulaire profils sauvegardé: {chemin}/repartition_profils_circulaire.png")


def creer_graphique_barres_profils(profil_counts, chemin):
    """Crée un graphique en barres horizontales pour une meilleure lisibilité"""
    
    plt.figure(figsize=(12, max(6, len(profil_counts) * 0.4)))
    
    total_clients = sum(profil_counts.values)
    
    # Trier par ordre décroissant pour les barres
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    
    # Créer des couleurs dégradées
    colors = plt.cm.Set3(np.linspace(0, 1, len(profil_counts_sorted)))
    
    # Barres horizontales
    bars = plt.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values,
                    color=colors, edgecolor='white', linewidth=1.5)
    
    plt.yticks(range(len(profil_counts_sorted)), profil_counts_sorted.index, fontsize=10)
    plt.xlabel('Nombre de clients', fontsize=12, fontweight='bold')
    plt.title(f'Répartition des {len(profil_counts)} profils clients\nTotal: {total_clients} clients', 
              fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    # Ajouter les valeurs et pourcentages
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        plt.text(count + total_clients * 0.02, i, 
                f'{count} clients ({percentage:.1f}%)', 
                va='center', fontsize=10, fontweight='bold')
    
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(f"{chemin}/repartition_profils_barres.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphique barres profils sauvegardé: {chemin}/repartition_profils_barres.png")


def creer_graphiques_tous_profils(stats_clients, profil_counts, chemin):
    """Crée un graphique avec tous les profils (pour les cas avec + de 2 profils)"""
    
    if len(profil_counts) <= 2:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse complète des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
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
    if 'montant_total' in stats_clients.columns:
        total_par_profil = stats_clients.groupby('profil')['montant_total'].sum().sort_values()
        total_par_profil = total_par_profil / 1_000_000  # Convertir en millions
        colors = [BLEU_EXCELLIA if i % 2 == 0 else ROSE_EXCELLIA for i in range(len(total_par_profil))]
        ax2.barh(total_par_profil.index, total_par_profil.values, color=colors, edgecolor='white')
        ax2.set_title('Montant total par profil (millions TND)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Montant total (millions)')
        
        # Ajouter les valeurs
        for i, (profil, val) in enumerate(total_par_profil.items()):
            ax2.text(val + 0.01, i, f'{val:.2f}M', va='center', fontsize=9)
    
    # 3. Fréquence moyenne par profil
    ax3 = axes[1, 0]
    if 'nb_transactions' in stats_clients.columns:
        freq_par_profil = stats_clients.groupby('profil')['nb_transactions'].mean().sort_values()
        ax3.bar(freq_par_profil.index, freq_par_profil.values, color=ROSE_EXCELLIA, edgecolor='white')
        ax3.set_title('Nombre moyen de transactions par profil', fontsize=12, fontweight='bold')
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax3.set_ylabel('Nombre de transactions')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Ajouter les valeurs sur les barres
        for i, (profil, val) in enumerate(freq_par_profil.items()):
            ax3.text(i, val + 0.5, f'{val:.0f}', ha='center', fontsize=9)
    
    # 4. Montant moyen par transaction par profil
    ax4 = axes[1, 1]
    if 'montant_moyen' in stats_clients.columns:
        montant_moyen_par_profil = stats_clients.groupby('profil')['montant_moyen'].mean().sort_values()
        ax4.bar(montant_moyen_par_profil.index, montant_moyen_par_profil.values, color=BLEU_EXCELLIA, edgecolor='white')
        ax4.set_title('Montant moyen par transaction (TND)', fontsize=12, fontweight='bold')
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax4.set_ylabel('Montant moyen (TND)')
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Ajouter les valeurs sur les barres
        for i, (profil, val) in enumerate(montant_moyen_par_profil.items()):
            ax4.text(i, val + 5, f'{val:.0f}', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_tous_profils.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graphique tous profils sauvegardé: {chemin}/graphiques_tous_profils.png")


def creer_graphiques_profils_avances(stats_clients, recommandations, chemin="output"):
    """
    Crée des graphiques avancés pour l'analyse des profils avec recommandations
    """
    if len(stats_clients) == 0:
        return
    
    if recommandations is None or len(recommandations) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Figure avec 3 graphiques
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Analyse des recommandations personnalisées', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    # 1. Distribution par type de recommandation (camembert avec couleurs personnalisées)
    ax1 = axes[0]
    if 'recommandation_type' in recommandations.columns:
        type_counts = recommandations['recommandation_type'].value_counts()
        
        # Utiliser les couleurs personnalisées
        colors_used = [TYPE_COLORS.get(t, '#95A5A6') for t in type_counts.index]
        
        # Créer des labels avec pourcentages
        total_rec = len(recommandations)
        labels = []
        for t, count in type_counts.items():
            percentage = (count / total_rec) * 100
            emoji = {
                'premium': '👑',
                'fidelisation': '❤️',
                'engagement': '🎯',
                'education': '📚',
                'standard': '📊',
                'acquisition': '🎁'
            }.get(t, '📌')
            labels.append(f'{emoji} {t.upper()}\n({count} clients, {percentage:.1f}%)')
        
        wedges, texts, autotexts = ax1.pie(
            type_counts.values,
            labels=labels,
            autopct='',
            colors=colors_used,
            startangle=90,
            textprops={'fontsize': 9, 'fontweight': 'bold'}
        )
        ax1.set_title('Type de recommandations', fontsize=12, fontweight='bold')
    
    # 2. Montant total par type (barres horizontales avec couleurs)
    ax2 = axes[1]
    if 'recommandation_type' in recommandations.columns and 'montant_total' in recommandations.columns:
        total_par_type = recommandations.groupby('recommandation_type')['montant_total'].sum().sort_values()
        colors_used = [TYPE_COLORS.get(t, '#95A5A6') for t in total_par_type.index]
        
        bars = ax2.barh(range(len(total_par_type)), total_par_type.values / 1_000_000, 
                        color=colors_used, edgecolor='white', linewidth=1)
        ax2.set_yticks(range(len(total_par_type)))
        ax2.set_yticklabels([t.upper() for t in total_par_type.index], fontsize=10)
        ax2.set_xlabel('Montant total (millions TND)', fontsize=11)
        ax2.set_title('Montant total par type', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Ajouter les valeurs
        for i, (t, val) in enumerate(total_par_type.items()):
            ax2.text(val / 1_000_000 + 0.01, i, f'{val/1_000_000:.2f}M', 
                    va='center', fontsize=9, fontweight='bold')
    
    # 3. Nombre de clients par type (barres horizontales)
    ax3 = axes[2]
    if 'recommandation_type' in recommandations.columns:
        clients_par_type = recommandations.groupby('recommandation_type').size().sort_values()
        colors_used = [TYPE_COLORS.get(t, '#95A5A6') for t in clients_par_type.index]
        
        bars = ax3.barh(range(len(clients_par_type)), clients_par_type.values, 
                        color=colors_used, edgecolor='white', linewidth=1)
        ax3.set_yticks(range(len(clients_par_type)))
        ax3.set_yticklabels([t.upper() for t in clients_par_type.index], fontsize=10)
        ax3.set_xlabel('Nombre de clients', fontsize=11)
        ax3.set_title('Nombre de clients par type', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Ajouter les valeurs
        for i, (t, count) in enumerate(clients_par_type.items()):
            ax3.text(count + 5, i, str(count), va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/analyse_recommandations_type.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Graphique recommandations sauvegardé: {chemin}/analyse_recommandations_type.png")
    
    # Créer une heatmap des recommandations par profil
    creer_heatmap_recommandations(recommandations, chemin)


def creer_heatmap_recommandations(recommandations, chemin):
    """Crée une heatmap des types de recommandations par profil"""
    
    if 'profil' not in recommandations.columns or 'recommandation_type' not in recommandations.columns:
        return
    
    # Créer une matrice croisée
    cross_tab = pd.crosstab(recommandations['profil'], recommandations['recommandation_type'])
    
    if len(cross_tab) > 0 and len(cross_tab.columns) > 0:
        plt.figure(figsize=(max(12, len(cross_tab.columns) * 0.8), 
                           max(8, len(cross_tab.index) * 0.4)))
        
        # Créer la heatmap
        im = plt.imshow(cross_tab.values, cmap='Reds', aspect='auto', interpolation='nearest')
        
        # Configurer les axes
        plt.xticks(range(len(cross_tab.columns)), 
                   [t.upper() for t in cross_tab.columns], 
                   rotation=45, ha='right', fontsize=10)
        plt.yticks(range(len(cross_tab.index)), cross_tab.index, fontsize=9)
        
        plt.xlabel('Type de recommandation', fontsize=12, fontweight='bold')
        plt.ylabel('Profil client', fontsize=12, fontweight='bold')
        plt.title('Correspondance entre profils et types de recommandations', 
                  fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        
        # Ajouter les valeurs dans chaque case
        for i in range(len(cross_tab.index)):
            for j in range(len(cross_tab.columns)):
                value = cross_tab.values[i, j]
                if value > 0:
                    text_color = 'white' if value > cross_tab.values.max() / 2 else 'black'
                    plt.text(j, i, str(value), ha='center', va='center', 
                            color=text_color, fontsize=10, fontweight='bold')
        
        plt.colorbar(im, label="Nombre de clients")
        plt.tight_layout()
        plt.savefig(f"{chemin}/heatmap_recommandations_profils.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ Heatmap recommandations sauvegardée: {chemin}/heatmap_recommandations_profils.png")


# Fonction principale pour la compatibilité
def creer_graphiques_principaux(df_trans_clients, df_stats_clients, profil_counts, chemin):
    """Fonction principale appelée par main.py"""
    creer_graphiques(df_trans_clients, df_stats_clients, profil_counts, chemin)
    if len(profil_counts) > 2:
        creer_graphiques_tous_profils(df_stats_clients, profil_counts, chemin)