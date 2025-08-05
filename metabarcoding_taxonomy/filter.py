#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metabarcoding_taxonomy.filter
노이즈 분류군 제거 + taxon 문자열 절단
"""
from __future__ import annotations
import os, re
import pandas as pd
from .base import MetabarcodingBase


class TaxonomyFilter(MetabarcodingBase):
    """필터링·전처리 담당"""

    # ─────────────────────────── 필터 규칙 ───────────────────────────
    def is_filtered_taxon(self, taxon: str, target_level: int = None) -> bool:
        segs = taxon.split(";")
        lower = taxon.lower()

        # 기존 조건들
        if "incertae" in lower or taxon.endswith("_sp"):
            return True
        if re.search(r"[0-9\-]", taxon):
            return True
        if any(k in lower for k in (
            "uncultured", "unidentified", "candidum",
            "candidatus", "metagenome"
        )):
            return True
        if re.search(r"[^A-Za-z0-9_;]", taxon):
            return True

        # === 강화된 빈 분류 레벨 패턴 검사 ===
        if target_level is not None:
            # 해당 레벨에서 빈 값("__") 체크 (0-based index)
            if len(segs) > target_level and segs[target_level] == "__":
                return True
            
            # 해당 레벨 이후 모든 레벨이 빈 값인지 체크
            if len(segs) > target_level:
                remaining_levels = segs[target_level:]
                if all(s == "__" for s in remaining_levels):
                    return True
        else:
            # 기존 로직 (하위 호환성)
            if len(segs) >= 3 and all(s == "__" for s in segs[2:]):
                return True
            if len(segs) >= 2 and all(s == "__" for s in segs[1:]):
                return True
        
        return False

    def truncate_taxonomy(self, taxon: str) -> str:
        parts, kept = taxon.split(";"), []
        for p in parts:
            lp = p.lower()
            if (p == "__" or "incertae" in lp or p.endswith("_sp") or
                re.search(r"[0-9\-]", p) or
                any(k in lp for k in (
                    "uncultured", "unidentified", "candidum",
                    "candidatus", "metagenome"
                )) or
                re.search(r"[^A-Za-z0-9_;]", p)):
                break
            kept.append(p)
        return ";".join(kept)

    # ─────────────────────────── 분류군 라벨 처리 ───────────────────────────
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

    # ─────────────────────────── 파일 처리 ───────────────────────────
    def filter_and_truncate(self, df: pd.DataFrame, src: str):
        self.log(f"Processing {src}")
        
        # 파일명에서 레벨 추출
        filename = os.path.basename(src)
        level_match = re.search(r'level-(\d+)', filename)
        target_level = int(level_match.group(1)) - 1 if level_match else None  # 0-based index
        
        if target_level is not None:
            self.log(f" Target level: {target_level + 1} (index: {target_level})")
        else:
            self.log(f" Target level: auto-detect")
        
        sample_col = self.sample_col or df.columns[0]
        taxa_cols = df.columns.drop(sample_col)

        # 레벨별 필터링 적용
        filtered = [c for c in taxa_cols if self.is_filtered_taxon(c, target_level)]
        retained = [c for c in taxa_cols if c not in filtered]
        
        self.log(f" Columns total={len(taxa_cols)}, "
                 f"filtered={len(filtered)}, retained={len(retained)}")

        # 결과 DataFrame
        df_filtered = df[[sample_col] + filtered]
        df_retained = df[[sample_col] + retained]
        df_trunc    = df.copy()
        df_trunc.columns = [sample_col] + [self.truncate_taxonomy(c) for c in taxa_cols]

        # 통계 출력
        total = df[taxa_cols].to_numpy().sum()
        fsum  = df_filtered[filtered].to_numpy().sum() if filtered else 0
        self.log(f" Total={total}, filtered={fsum} ({fsum/total*100:.2f}%)")

        base = os.path.splitext(os.path.basename(src))[0]
        out_dir = os.path.dirname(src)
        df_filtered.to_csv(f"{out_dir}/{base}_filtered.csv",  index=False)
        df_retained.to_csv(f"{out_dir}/{base}_retained.csv",  index=False)
        df_trunc.to_csv   (f"{out_dir}/{base}_truncated.csv", index=False)

    def process_all_files(self):
        for fp in self.file_paths:
            self.filter_and_truncate(pd.read_csv(fp), fp)
