#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metabarcoding_taxonomy.workflow
end-to-end 실행 래퍼
"""
from __future__ import annotations
from .visualizer import TaxonomyVisualizer


class MetabarcodingWorkflow(TaxonomyVisualizer):
    """필터링 → 통계 → 시각화 일괄 실행"""
    def run_all(self):
        self.log("=== MetabarcodingWorkflow start ===")
        self.process_all_files()
        self.compute_unclassified_stats()
        self.plot_well_classified()
        self.plot_taxa_retained()
        self.plot_cumulative_barplots()
        self.log("=== MetabarcodingWorkflow complete ===")