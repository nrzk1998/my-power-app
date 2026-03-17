# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

def get_power_cols(df):
    """時間軸列のみを抽出"""
    return [c for c in df.columns if ":" in str(c)]

def create_combined_report(final_df, k_auto):
    """Step 1, 2, 3 と 内訳を1枚の画像に統合"""
    power_cols = get_power_cols(final_df)
    cluster_means = final_df.groupby('Cluster')[power_cols].mean()
    cluster_counts = final_df['Cluster'].value_counts()
    cmap = plt.get_cmap('tab10')
    
    # グラフ用色設定
    season_colors = {'Cooling': '#1f77b4', 'Intermediate': '#e2e2e2', 'Heating': '#ff7f0e'}
    seasons_order = ['Cooling', 'Intermediate', 'Heating']
    
    time_labels = power_cols
    x_ticks = np.arange(0, len(time_labels), 4)
    x_labels = [time_labels[i] for i in x_ticks]

    fig = plt.figure(figsize=(16, 22))
    gs = gridspec.GridSpec(4, k_auto, height_ratios=[1, 1, 1, 0.8], hspace=0.35)

    # --- Step 1: Raw Data ---
    ax1 = fig.add_subplot(gs[0, :])
    for i in range(len(final_df)):
        ax1.plot(time_labels, final_df[power_cols].iloc[i], color='gray', alpha=0.15, lw=0.5)
    ax1.set_title("Step 1: Raw Daily Power Consumption (Total 365 days)", fontsize=16, fontweight='bold')
    ax1.set_ylabel("Power Intensity [Wh/sqm]")
    ax1.grid(True, linestyle='--', alpha=0.3)

    # --- Step 2: Clustered Data ---
    ax2 = fig.add_subplot(gs[1, :], sharex=ax1)
    for cid in sorted(final_df['Cluster'].unique()):
        c_color = cmap((cid-1) % 10)
        c_data = final_df[final_df['Cluster'] == cid][power_cols]
        for i in range(len(c_data)):
            ax2.plot(time_labels, c_data.iloc[i], color=c_color, alpha=0.25, lw=0.5)
    ax2.set_title(f"Step 2: Daily Curves Colored by Cluster (k={k_auto})", fontsize=16, fontweight='bold')
    ax2.set_ylabel("Power Intensity [Wh/sqm]")
    ax2.grid(True, linestyle='--', alpha=0.3)

    # --- Step 3: Cluster Centroids ---
    ax3 = fig.add_subplot(gs[2, :], sharex=ax1)
    for i, cid in enumerate(sorted(cluster_means.index)):
        c_color = cmap(i % 10)
        ax3.plot(time_labels, cluster_means.loc[cid], 
                 label=f"Cluster {cid} (n={cluster_counts[cid]}d)", color=c_color, lw=4)
    ax3.set_title("Step 3: Cluster Centroids (Representative Patterns)", fontsize=16, fontweight='bold')
    ax3.set_ylabel("Power Intensity [Wh/sqm]")
    ax3.set_xticks(x_ticks)
    ax3.set_xticklabels(x_labels)
    ax3.legend(loc='upper right', shadow=True)
    ax3.grid(True, linestyle='--', alpha=0.5)

    # --- Step 4: Breakdown ---
    y_limit_sub = cluster_counts.max() * 1.15
    for i, cid in enumerate(sorted(final_df['Cluster'].unique())):
        ax_sub = fig.add_subplot(gs[3, i])
        c_data = final_df[final_df['Cluster'] == cid]
        # DayTypeとSeasonで集計
        comp = c_data.groupby(['DayType', 'Season']).size().unstack(fill_value=0)
        
        # 欠損インデックスの補完
        for t in ['Weekday', 'Weekend']:
            if t not in comp.index: comp.loc[t] = 0
        for s in seasons_order:
            if s not in comp.columns: comp[s] = 0
        comp = comp.reindex(index=['Weekday', 'Weekend'], columns=seasons_order)

        bottom = np.zeros(2)
        for s in seasons_order:
            ax_sub.bar(comp.index, comp[s], bottom=bottom, color=season_colors[s], edgecolor='white')
            bottom += comp[s]

        ax_sub.set_title(f"Cluster {cid}", color=cmap(i % 10), fontweight='bold')
        ax_sub.set_ylim(0, y_limit_sub)
        if i != 0: ax_sub.set_yticklabels([])
        if i == k_auto - 1: ax_sub.legend(seasons_order, title="Season", loc='upper left', bbox_to_anchor=(1, 1))
        ax_sub.grid(axis='y', linestyle=':', alpha=0.6)

    return fig

import calendar
import matplotlib.patches as patches

# 日曜始まりに設定
calendar.setfirstweekday(calendar.SUNDAY)

def create_calendar_report(final_df):
    """
    カレンダー形式でクラスタと気象・休日を表示するレポートを作成
    """
    unique_months = final_df.index.to_period('M').unique()
    n_months = len(unique_months)
    
    fig, axes = plt.subplots(nrows=n_months, ncols=2, figsize=(13.3, 22))
    if n_months == 1: axes = np.expand_dims(axes, axis=0)
    
    cmap = plt.get_cmap('tab10')

    def draw_month_ax(ax, month_df, cal, mode):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, len(cal))
        ax.invert_yaxis()
        ax.axis('off')
        
        # 曜日ラベル
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for ci, day_name in enumerate(days):
            ax.text(ci + 0.5, -0.5, day_name, ha='center', va='center', fontsize=9, fontweight='bold')

        for ri, week in enumerate(cal):
            for ci, day in enumerate(week):
                if day == 0: continue
                
                day_data = month_df[month_df.index.day == day]
                if day_data.empty:
                    color = "white"
                else:
                    row = day_data.iloc[0]
                    if mode == 'cluster':
                        # 左側：クラスタベース
                        cid = row['Cluster']
                        color = cmap((int(cid)-1) % 10) if pd.notna(cid) else "white"
                    else:
                        # 右側：気象・休日ベース (参考コードのロジックを適用)
                        if row['IsHoliday']:
                            color = "royalblue"
                        elif row['Season'] in ['Cooling', 'Heating']: # 内部のSeason名(Cooling/Heating)に対応
                            color = "tomato"
                        else:
                            color = "darkgrey"

                ax.add_patch(plt.Rectangle((ci, ri), 1, 1, facecolor=color, edgecolor='white', linewidth=1))
                # 日付の文字（白固定）
                ax.text(ci + 0.5, ri + 0.5, str(day), ha='center', va='center', color='white', fontsize=10, fontweight='bold')

    for i, ym in enumerate(unique_months):
        year, month = ym.year, ym.month
        month_df = final_df[(final_df.index.year == year) & (final_df.index.month == month)]
        cal = calendar.monthcalendar(year, month)
        
        draw_month_ax(axes[i, 0], month_df, cal, mode='cluster')
        axes[i, 0].set_title(f"{year}/{month:02d} [Cluster]", fontsize=12, pad=20, fontweight='bold')

        draw_month_ax(axes[i, 1], month_df, cal, mode='weather')
        axes[i, 1].set_title(f"{year}/{month:02d} [Weather]", fontsize=12, pad=20, fontweight='bold')

    plt.subplots_adjust(hspace=0.6, wspace=0.1)
    return fig