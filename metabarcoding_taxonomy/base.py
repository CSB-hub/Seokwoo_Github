#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metabarcoding_taxonomy.base
공통 I/O · 로깅 · 유틸리티
"""
from __future__ import annotations
import re, os, glob, datetime
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Arial"


class MetabarcodingBase:
    """모든 분석 클래스의 부모"""

    DEFAULT_LEVEL_LABELS = [
        "Kingdom", "Phylum", "Class",
        "Order", "Family", "Genus", "Species"
    ]

    def __init__(
        self,
        input_dir: str = ".",
        level_pattern: str = "level-*.csv",
        sample_col: str | None = None,
        level_labels: list[str] | None = None,
        sample_name_mapping: dict[str, str] | None = None,
    ):
        self.input_dir = input_dir
        self.sample_col = sample_col
        self.sample_name_mapping = sample_name_mapping or {}

        # level-N.csv 경로 수집
        pattern = os.path.join(input_dir, level_pattern)
        self.file_paths = sorted(
            fp for fp in glob.glob(pattern)
            if re.fullmatch(r"level-\d+\.csv", os.path.basename(fp))
        )
        if not self.file_paths:
            raise FileNotFoundError(f"No level files found in {input_dir}")

        self.level_names = [
            os.path.splitext(os.path.basename(fp))[0]  # level-1 …
            for fp in self.file_paths
        ]

        # 레벨 라벨 길이 검증
        if level_labels:
            if len(level_labels) != len(self.level_names):
                raise ValueError("level_labels length must match number of levels")
            self.level_labels = level_labels
        else:
            self.level_labels = self.DEFAULT_LEVEL_LABELS[: len(self.level_names)]

        self.log(f"Initialized with levels: {self.level_names}")

    # ---------- 공통 유틸 ----------
    def log(self, msg: str):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] {msg}")

    def map_sample_names(self, names: list[str]) -> list[str]:
        return [self.sample_name_mapping.get(n, n) for n in names]

    @staticmethod
    def last_tax_label(taxon: str) -> str:
        """세미콜론 표기에서 마지막 라벨만 추출"""
        if taxon == "Other":
            return "Other"
        last = taxon.split(";")[-1]
        return last.split("__", 1)[1] if "__" in last else last
