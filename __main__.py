#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메타바코딩 분석 실행 스크립트
"""

from metabarcoding_taxonomy import MetabarcodingWorkflow

# 샘플 이름 매핑 딕셔너리 정의
sample_mapping = {
    '0H': '0H',
    '6H': '6H', 
    '12H': '12H',
    '18H': '18H',
    '24H': '24H'
}

# 워크플로우 실행
workflow = MetabarcodingWorkflow(
    input_dir='/Users/bbogoo/Desktop/메타바코딩/marine_media/marine_media_csv',
    level_pattern='level-*.csv',
    level_labels=['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species'],
    sample_name_mapping=sample_mapping
)

if __name__ == '__main__':
    # 기본 분석 실행
    workflow.run_all()
    
    # Supplementary figure 생성 (새로 추가)
    print("Generating supplementary figures...")
    workflow.supplementary_figure_all_details()
    print("All analyses completed!")
