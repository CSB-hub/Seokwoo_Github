#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metabarcoding_taxonomy.visualizer
통계 결과 시각화
"""
from __future__ import annotations
import os, glob, numpy as np, pandas as pd, matplotlib.pyplot as plt
from .statistics import TaxonomyStatistics


class TaxonomyVisualizer(TaxonomyStatistics):
    """well-classified·retained 비율 & 누적 바플롯"""
    
    # ─────────── 분류군 라벨 처리 ───────────
    def last_tax_label_with_readable_prefix(self, tax_string):
        """분류학적 경로에서 마지막 분류군명을 읽기 쉬운 접두사와 함께 추출"""
        if tax_string == "Other":
            return "Other"
        
        # 접두사 매핑
        prefix_map = {
            'k__': 'K: ',    # Kingdom
            'p__': 'P: ',    # Phylum  
            'c__': 'C: ',    # Class
            'o__': 'O: ',    # Order
            'f__': 'F: ',    # Family
            'g__': 'G: ',    # Genus
            's__': 'S: '     # Species
        }
        
        parts = tax_string.split(';')
        last_part = parts[-1]
        
        # 접두사 변환
        for prefix, readable in prefix_map.items():
            if last_part.startswith(prefix):
                name = last_part.replace(prefix, '')
                return f"{readable}{name}"
        
        return last_part  # 접두사가 없는 경우 그대로 반환
    
    # ─────────── well-classified ───────────
    def plot_well_classified(self):
        if self.stats_df is None:
            self.compute_unclassified_stats()

        self.log("Plotting well-classified lines…")
        df = 1 - self.stats_df      # well-classified 비율
        
        # Phylum부터 시작 (Kingdom 제외)
        phylum_labels = self.level_labels[1:]  # Kingdom 제외하고 Phylum부터
        df_phylum = df.iloc[:, 1:]  # Kingdom 컬럼 제외
        
        fig, ax = plt.subplots(figsize=(6, 5), dpi=450)
        for s in df_phylum.index:
            ax.plot(phylum_labels, df_phylum.loc[s]*100,
                    marker="o", linewidth=3, markersize=10, label=s)
        ax.set_ylim(-5, 105)
        ax.set_ylabel("Well-classified (%)", fontsize=16)
        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.grid(True, ls="--", alpha=.4)
        ax.legend(fontsize=14)
        fig.tight_layout()
        fig.savefig(os.path.join(self.input_dir, "Well_classified_proportion.pdf"))
        plt.close(fig)

    # ─────────── retained taxa ───────────
    def plot_taxa_retained(self):
        df = self.compute_taxa_counts()
        self.log("Plotting retained taxa ratio…")
        
        # Phylum부터 시작 (Kingdom 제외)
        phylum_labels = self.level_labels[1:]  # Kingdom 제외하고 Phylum부터
        df_phylum = df.iloc[1:]  # Kingdom 값 제외
        
        fig, ax = plt.subplots(figsize=(6, 5), dpi=450)
        ax.plot(phylum_labels, df_phylum.values*100, marker="o", linewidth=3, markersize=10)
        ax.set_ylim(-5, 105)
        ax.set_ylabel("Retained taxa (%)", fontsize=16)
        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.grid(True, ls="--", alpha=.4)
        fig.tight_layout()
        fig.savefig(os.path.join(self.input_dir, "Retained_taxa_ratio.pdf"))
        plt.close(fig)

    # ─────────── 누적 바플롯 (기본) ───────────
    def plot_cumulative_barplots(self, dpi=450, top_n=10):
        self.log("Plotting cumulative barplots…")
        for fp in sorted(
            glob.glob(os.path.join(self.input_dir, "level-*_*truncated.csv"))
        ):
            self._single_barplot(fp, dpi, top_n)

    def _single_barplot(self, fp: str, dpi: int, top_n: int):
        level = os.path.basename(fp).split("_")[0]   # level-1
        df = pd.read_csv(fp)
        sample_col = df.columns[0]
        counts = df.set_index(sample_col)
        counts.index = self.map_sample_names(counts.index.tolist())

        rel = counts.div(counts.sum(axis=1), axis=0) * 100
        means = rel.mean(axis=0).sort_values(ascending=False)
        top = means.index[:top_n]
        other = (100 - rel[top].sum(axis=1)).clip(lower=0)
        plot_df = rel[top].copy()
        if other.any():
            plot_df["Other"] = other

        # 고정된 색상 리스트 사용
        base_colors = [
            '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
            '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
            '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'
        ]

        colors = base_colors[:len(plot_df.columns)]
        
        if "Other" in plot_df.columns:
            colors[-1] = '#000000'  # Other는 검은색으로 고정

        fig, ax = plt.subplots(figsize=(8, 5), dpi=dpi)
        bottom = np.zeros(len(plot_df))
        x = np.arange(len(plot_df))
        for c, col in enumerate(plot_df.columns):
            ax.bar(x, plot_df[col], bottom=bottom,
                   label=self.last_tax_label_with_readable_prefix(col),
                   color=colors[c])
            bottom += plot_df[col].values

        ax.set_xticks(x)
        ax.set_xticklabels(plot_df.index, rotation=30, ha="right", fontsize=14)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Relative abundance (%)", fontsize=14)
        ax.tick_params(axis='y', which='major', labelsize=14)
        ax.grid(axis="y", ls="--", alpha=.3)
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=14)
        fig.tight_layout(rect=[0, 0, 0.85, 1])
        fig.savefig(os.path.join(self.input_dir, f"{level}_barplot.pdf"), dpi=450)
        plt.close(fig)

    # ─────────── 누적 바플롯 (Supplementary - 모든 분류군) ───────────
    def supplementary_figure_all_details(self, dpi=450):
        """모든 분류군을 표시하는 Supplementary Figure용 누적 바플롯 (Others 그룹핑 없음)"""
        self.log("Plotting supplementary cumulative barplots (all taxa)…")
        for fp in sorted(
            glob.glob(os.path.join(self.input_dir, "level-*_*truncated.csv"))
        ):
            self._single_barplot_full(fp, dpi)

    def _single_barplot_full(self, fp: str, dpi: int):
        """모든 분류군을 개별적으로 표시하는 바플롯 (Others 그룹핑 없음)"""
        level = os.path.basename(fp).split("_")[0]   # level-1
        df = pd.read_csv(fp)
        sample_col = df.columns[0]
        counts = df.set_index(sample_col)
        counts.index = self.map_sample_names(counts.index.tolist())

        rel = counts.div(counts.sum(axis=1), axis=0) * 100
        means = rel.mean(axis=0).sort_values(ascending=False)
        
        # Others 그룹핑 없이 모든 분류군 사용
        plot_df = rel[means.index].copy()  # abundance 순으로 정렬된 모든 분류군
        
        # 15개 색상을 순환하여 사용
        base_colors = [
            '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
            '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
            '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'
        ]
        
        # 분류군 수가 15개보다 많으면 색상을 순환하여 사용
        colors = [base_colors[i % len(base_colors)] for i in range(len(plot_df.columns))]

        fig, ax = plt.subplots(figsize=(8, 5), dpi=dpi)
        bottom = np.zeros(len(plot_df))
        x = np.arange(len(plot_df))
        
        # 평균 abundance 기준 상위 10개만 범례에 표시하기 위한 정보
        top_10_taxa = means.index[:10]
        
        for c, col in enumerate(plot_df.columns):
            # 상위 10개에 포함되는 경우에만 범례 라벨 추가
            label = self.last_tax_label_with_readable_prefix(col) if col in top_10_taxa else ""
            
            ax.bar(x, plot_df[col], bottom=bottom,
                   label=label if label else None,  # 빈 라벨은 None으로 처리
                   color=colors[c])
            bottom += plot_df[col].values

        ax.set_xticks(x)
        ax.set_xticklabels(plot_df.index, rotation=30, ha="right", fontsize=14)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Relative abundance (%)", fontsize=14)
        ax.tick_params(axis='y', which='major', labelsize=14)
        ax.grid(axis="y", ls="--", alpha=.3)
        
        # 범례는 상위 10개에 대해서만 표시
        handles, labels = ax.get_legend_handles_labels()
        if handles:  # 범례 항목이 있는 경우에만 범례 표시
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=14)
        
        fig.tight_layout(rect=[0, 0, 0.85, 1])
        fig.savefig(os.path.join(self.input_dir, f"{level}_barplot_Supple.pdf"), dpi=450)
        plt.close(fig)
