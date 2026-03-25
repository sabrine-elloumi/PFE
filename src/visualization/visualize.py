import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROSE_EXCELLIA = '#E6007E'
BLEU_EXCELLIA = '#302383'
GRIS_CLAIR = '#F5F5F5'

TYPE_COLORS = {
    'premium': ROSE_EXCELLIA,
    'fidelisation': BLEU_EXCELLIA,
    'engagement': '#FF6B6B',
    'education': '#4ECDC4',
    'standard': '#95A5A6',
    'acquisition': '#2ECC71'
}

def creer_graphiques(df_trans, df_stats, profil_counts, chemin):
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('Analyse des transactions - Smart Personal Finance Wallet', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    plt.subplot(2, 3, 1)
    top10 = df_stats.nlargest(10, 'montant_total').copy()
    top10 = top10.sort_values('montant_total', ascending=True)
    top10['client'] = ['Client ' + str(i+1) for i in range(len(top10)-1, -1, -1)]
    top10['montant_total_millions'] = top10['montant_total'] / 1_000_000
    
    max_val = top10['montant_total_millions'].max()
    
    colors_top10 = [ROSE_EXCELLIA if i < 5 else BLEU_EXCELLIA for i in range(len(top10))]
    bars = plt.barh(top10['client'], top10['montant_total_millions'], 
                    color=colors_top10, edgecolor='white', linewidth=1.5)
    plt.title('Top 10 clients par montant total', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant total (millions TND)', fontsize=11)
    plt.ylabel('Client', fontsize=11)
    
    for bar, val in zip(bars, top10['montant_total'] / 1_000_000):
        width = bar.get_width()
        if width > 0:
            plt.text(width + max_val * 0.01, bar.get_y() + bar.get_height()/2, f'{val:.2f}M', 
                    ha='left', va='center', fontsize=9, fontweight='bold')
    
    plt.subplot(2, 3, 2)
    n_profils = len(profil_counts)
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    colors_bar = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(n_profils)]
    
    bars = plt.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values,
                    color=colors_bar, edgecolor='white', linewidth=1.5)
    plt.yticks(range(len(profil_counts_sorted)), profil_counts_sorted.index, fontsize=9)
    plt.title(f'Repartition des {n_profils} profils clients', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Nombre de clients', fontsize=11)
    
    total_clients = sum(profil_counts_sorted.values)
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        plt.text(count + total_clients * 0.01, i, f'{count} ({percentage:.1f}%)', 
                va='center', fontsize=8, fontweight='bold')
    
    plt.subplot(2, 3, 3)
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        moyenne_par_profil = df_avec_profil.groupby('profil')['amount'].mean().round(0)
        moyenne_par_profil = moyenne_par_profil.sort_values(ascending=False)
        
        if len(moyenne_par_profil) > 6:
            moyenne_par_profil = moyenne_par_profil.head(6)
        
        bar_colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(moyenne_par_profil))]
        
        bars = plt.bar(range(len(moyenne_par_profil)), moyenne_par_profil.values,
                       color=bar_colors, edgecolor='white', linewidth=1.5)
        plt.title('Montant moyen par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
        plt.xlabel('Profil', fontsize=11)
        plt.ylabel('Montant moyen (TND)', fontsize=11)
        plt.xticks(range(len(moyenne_par_profil)), moyenne_par_profil.index, rotation=15, ha='right', fontsize=8)
        
        for bar, val in zip(bars, moyenne_par_profil.values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + max(moyenne_par_profil.values) * 0.02,
                    f'{val:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.subplot(2, 3, 4)
    n, bins, patches = plt.hist(df_trans['amount'], bins=50, edgecolor='white', 
                                alpha=0.8, log=True, color=ROSE_EXCELLIA)
    plt.title('Distribution des montants', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    plt.xlabel('Montant (TND)', fontsize=11)
    plt.ylabel('Frequence (log)', fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.subplot(2, 3, 5)
    if 'mois_annee' in df_trans.columns:
        evolution = df_trans.groupby('mois_annee')['amount'].sum() / 1_000_000
        if len(evolution) > 0:
            plt.plot(range(len(evolution)), evolution.values, 
                     linewidth=2, color=BLEU_EXCELLIA, marker='o', markersize=4)
            plt.fill_between(range(len(evolution)), evolution.values, alpha=0.2, color=ROSE_EXCELLIA)
            plt.title('Evolution mensuelle des montants', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
            plt.xlabel('Mois', fontsize=11)
            plt.ylabel('Montant total (millions TND)', fontsize=11)
            
            step = max(1, len(evolution) // 6)
            plt.xticks(range(0, len(evolution), step), 
                       [str(d) for d in evolution.index[::step]], rotation=45)
            plt.grid(True, alpha=0.3)
    
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
    
    print(f"  Graphiques principaux sauvegardes: {chemin}/graphiques_excellia_principaux.png")
    
    creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin)


def creer_graphiques_detail(df_trans, df_stats, profil_counts, chemin):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Analyse detaillee des profils clients', fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    if 'profil' in df_stats.columns:
        df_avec_profil = pd.merge(df_trans, df_stats[['client_id', 'profil']], 
                                  on='client_id', how='left')
        
        top_profils = profil_counts.nlargest(5).index.tolist()
        
        data_to_plot = []
        labels = []
        for profil in top_profils:
            data = df_avec_profil[df_avec_profil['profil'] == profil]['amount']
            if len(data) > 0:
                data_to_plot.append(data)
                short_name = profil[:25] + '...' if len(profil) > 25 else profil
                labels.append(short_name)
        
        if data_to_plot:
            box_colors = [ROSE_EXCELLIA, BLEU_EXCELLIA, ROSE_EXCELLIA, BLEU_EXCELLIA, ROSE_EXCELLIA]
            
            bp = axes[0].boxplot(data_to_plot, labels=labels,
                                 patch_artist=True,
                                 boxprops=dict(facecolor=ROSE_EXCELLIA, color=BLEU_EXCELLIA, alpha=0.7),
                                 whiskerprops=dict(color=BLEU_EXCELLIA),
                                 capprops=dict(color=BLEU_EXCELLIA),
                                 medianprops=dict(color='white', linewidth=2),
                                 flierprops=dict(marker='o', markerfacecolor=ROSE_EXCELLIA,
                                                markersize=4, alpha=0.5))
            
            for i, patch in enumerate(bp['boxes']):
                patch.set_facecolor(box_colors[i % len(box_colors)])
                patch.set_alpha(0.7)
            
            axes[0].set_title('Distribution des montants par profil', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Profil', fontsize=11)
            axes[0].set_ylabel('Montant (TND)', fontsize=11)
            axes[0].set_yscale('log')
            axes[0].grid(True, alpha=0.3, axis='y')
            plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=15, ha='right', fontsize=9)
    
    ax2 = axes[1]
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    colors_pie = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(profil_counts_sorted))]
    
    bars = ax2.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values, 
                    color=colors_pie, edgecolor='white', linewidth=1.5, height=0.7)
    
    ax2.set_yticks(range(len(profil_counts_sorted)))
    ax2.set_yticklabels(profil_counts_sorted.index, fontsize=9)
    ax2.set_xlabel('Nombre de clients', fontsize=12, fontweight='bold')
    ax2.set_title('Repartition des clients par profil', fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    total_clients = sum(profil_counts_sorted.values)
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        ax2.text(count + total_clients * 0.01, i, 
                f'{count} clients ({percentage:.1f}%)', 
                va='center', fontsize=9, fontweight='bold')
    
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/graphiques_excellia_detail.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Graphiques detail sauvegardes: {chemin}/graphiques_excellia_detail.png")
    
    creer_graphique_barres_profils(profil_counts, chemin)


def creer_graphique_barres_profils(profil_counts, chemin):
    plt.figure(figsize=(12, max(6, len(profil_counts) * 0.4)))
    
    total_clients = sum(profil_counts.values)
    profil_counts_sorted = profil_counts.sort_values(ascending=True)
    colors = [ROSE_EXCELLIA if i % 2 == 0 else BLEU_EXCELLIA for i in range(len(profil_counts_sorted))]
    
    bars = plt.barh(range(len(profil_counts_sorted)), profil_counts_sorted.values,
                    color=colors, edgecolor='white', linewidth=1.5)
    
    plt.yticks(range(len(profil_counts_sorted)), profil_counts_sorted.index, fontsize=10)
    plt.xlabel('Nombre de clients', fontsize=12, fontweight='bold')
    plt.title(f'Repartition des {len(profil_counts)} profils clients\nTotal: {total_clients} clients', 
              fontsize=14, fontweight='bold', color=BLEU_EXCELLIA)
    
    for i, (profil, count) in enumerate(profil_counts_sorted.items()):
        percentage = (count / total_clients) * 100
        plt.text(count + total_clients * 0.02, i, 
                f'{count} clients ({percentage:.1f}%)', 
                va='center', fontsize=10, fontweight='bold')
    
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(f"{chemin}/repartition_profils_barres.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Graphique barres profils sauvegarde: {chemin}/repartition_profils_barres.png")


def creer_graphiques_profils_avances(stats_clients, recommandations, chemin="output"):
    if len(stats_clients) == 0 or recommandations is None or len(recommandations) == 0:
        return
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Analyse des recommandations personnalisees', 
                 fontsize=16, fontweight='bold', color=BLEU_EXCELLIA)
    
    ax1 = axes[0]
    if 'recommandation_type' in recommandations.columns:
        type_counts = recommandations['recommandation_type'].value_counts()
        colors_used = [TYPE_COLORS.get(t, ROSE_EXCELLIA) for t in type_counts.index]
        
        total_rec = len(recommandations)
        labels = []
        for t, count in type_counts.items():
            percentage = (count / total_rec) * 100
            emoji = {
                'premium': 'VIP',
                'fidelisation': 'FID',
                'engagement': 'ACT',
                'education': 'EDU',
                'standard': 'STD',
                'acquisition': 'NEW'
            }.get(t, t.upper())
            labels.append(f'{emoji}\n({count} clients, {percentage:.1f}%)')
        
        wedges, texts, autotexts = ax1.pie(type_counts.values, labels=labels, autopct='',
                colors=colors_used, startangle=90, textprops={'fontsize': 9, 'fontweight': 'bold'})
        ax1.set_title('Type de recommandations', fontsize=12, fontweight='bold')
    
    ax2 = axes[1]
    if 'recommandation_type' in recommandations.columns and 'montant_total' in recommandations.columns:
        total_par_type = recommandations.groupby('recommandation_type')['montant_total'].sum().sort_values()
        colors_used = [TYPE_COLORS.get(t, ROSE_EXCELLIA) for t in total_par_type.index]
        
        max_val = total_par_type.values.max()
        
        bars = ax2.barh(range(len(total_par_type)), total_par_type.values, 
                        color=colors_used, edgecolor='white', linewidth=1)
        ax2.set_yticks(range(len(total_par_type)))
        
        type_labels = []
        for t in total_par_type.index:
            emoji = {
                'premium': 'VIP',
                'fidelisation': 'FID',
                'engagement': 'ACT',
                'education': 'EDU',
                'standard': 'STD',
                'acquisition': 'NEW'
            }.get(t, t.upper())
            type_labels.append(emoji)
        
        ax2.set_yticklabels(type_labels, fontsize=10, fontweight='bold')
        ax2.set_xlabel('Montant total (TND)', fontsize=11)
        ax2.set_title('Montant total par type', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        for i, (t, val) in enumerate(total_par_type.items()):
            label = f'{val:,.0f} TND'
            ax2.text(val + max_val * 0.02, i, label, va='center', fontsize=9, fontweight='bold')
    
    ax3 = axes[2]
    if 'recommandation_type' in recommandations.columns:
        clients_par_type = recommandations.groupby('recommandation_type').size().sort_values()
        colors_used = [TYPE_COLORS.get(t, ROSE_EXCELLIA) for t in clients_par_type.index]
        
        bars = ax3.barh(range(len(clients_par_type)), clients_par_type.values, 
                        color=colors_used, edgecolor='white', linewidth=1)
        ax3.set_yticks(range(len(clients_par_type)))
        
        type_labels = []
        for t in clients_par_type.index:
            emoji = {
                'premium': 'VIP',
                'fidelisation': 'FID',
                'engagement': 'ACT',
                'education': 'EDU',
                'standard': 'STD',
                'acquisition': 'NEW'
            }.get(t, t.upper())
            type_labels.append(emoji)
        
        ax3.set_yticklabels(type_labels, fontsize=10, fontweight='bold')
        ax3.set_xlabel('Nombre de clients', fontsize=11)
        ax3.set_title('Nombre de clients par type', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        max_count = clients_par_type.values.max()
        for i, (t, count) in enumerate(clients_par_type.items()):
            ax3.text(count + max_count * 0.02, i, str(count), va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{chemin}/analyse_recommandations_type.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Graphique recommandations sauvegarde: {chemin}/analyse_recommandations_type.png")