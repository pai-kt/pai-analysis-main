"""의사결정지원시스템 · Streamlit 진입점.

실행:
    streamlit run app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 프로젝트 루트를 import path에 추가 (어디서 실행해도 src 패키지 인식)
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Streamlit Cloud / Linux 서버: matplotlib 캐시·GUI 백엔드 이슈 방지
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("MPLBACKEND", "Agg")

import streamlit as st

if os.environ.get("PAI_APP_MODE") != "mobile":
    st.set_page_config(page_title="의사결정지원시스템 · 토마토 대시보드", layout="wide")

# 모바일 모드용 최소 스타일
if os.environ.get("PAI_APP_MODE") == "mobile":
    st.markdown(
        """
        <style>
        .block-container { max-width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# streamlit run app.py → __main__ 에서만 UI 실행
if __name__ == "__main__" and os.environ.get("PAI_APP_MODE") != "mobile":
    from src.ui.desktop import run_desktop_ui

    run_desktop_ui()
