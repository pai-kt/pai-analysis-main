#!/usr/bin/env python3
"""참조 데이터(data/생육·환경·일사량)로 모델을 학습해 models/에 저장합니다.

사용법:
    python train_reference_models.py
"""
from model_store import train_and_save_all_models


if __name__ == "__main__":
    print("참조 데이터 기반 모델 학습을 시작합니다…")
    manifest = train_and_save_all_models()
    print(f"완료: {len(manifest['models'])}개 모델 저장 → models/")
