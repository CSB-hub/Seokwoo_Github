#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metabarcoding_taxonomy.statistics
필터링 결과 기반 통계
"""
from __future__ import annotations
import pandas as pd
from .filter import TaxonomyFilter


class TaxonomyStatistics(TaxonomyFilter):
    """미분류 비율 · retained taxa 비율 계산"""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.stats_df = None
        self.taxa_count_df = None

    # ───────────────── 미분류 비율 ─────────────────
    def compute_unclassified_stats(self) -> pd.DataFrame:
        self.log("Computing unclassified stats…")
        stats, sample_names = {}, None

        for fp, lvl in zip(self.file_paths, self.level_names):
            df = pd.read_csv(fp)
            sample_col = self.sample_col or df.columns[0]

            if sample_names is None:
                sample_names = df[sample_col].tolist()

            taxa_cols = df.columns.drop(sample_col)
            total = df[taxa_cols].sum(axis=1)
            filt_cols = [c for c in taxa_cols if self.is_filtered_taxon(c)]
            filt_sum = df[filt_cols].sum(axis=1) if filt_cols else 0
            stats[lvl] = (filt_sum / total.replace(0, pd.NA)).values
            self.log(f" Level {lvl} done")

        idx = self.map_sample_names(sample_names)
        self.stats_df = pd.DataFrame(stats, index=idx)
        return self.stats_df

    # ───────────────── retained taxa 개수 ─────────────────
    def compute_taxa_counts(self) -> pd.Series:
        self.log("Computing retained taxa column ratios…")
        ratios = {}
        for fp, lvl in zip(self.file_paths, self.level_names):
            df = pd.read_csv(fp)
            sample_col = self.sample_col or df.columns[0]
            taxa_cols = df.columns.drop(sample_col)
            retained = sum(not self.is_filtered_taxon(c) for c in taxa_cols)
            ratios[lvl] = retained / len(taxa_cols)
        self.taxa_count_df = pd.Series(ratios, name="retained_taxa_ratio")
        return self.taxa_count_df
