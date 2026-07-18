#!/usr/bin/env python3
"""총출하량 상위 10농가의 생육·환경·일사량으로 3~12주 모델을 학습합니다.

사용법:
    python train_reference_models.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.model_store import train_and_save_all_models


if __name__ == "__main__":
    print("기존 모델을 제거하고 선도 상위 10농가 기반 3~12주 모델 학습을 시작합니다…")
    manifest = train_and_save_all_models()
    print(f"완료: {len(manifest['models'])}개 모델 저장 → models/")
