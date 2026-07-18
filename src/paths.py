"""Project root paths (data/, models/)."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
FONTS_DIR = PROJECT_ROOT / "fonts"

# data/ 하위 용도별 폴더
MODEL_DATA_DIR = DATA_DIR / "모델학습"          # 선도 농가·모델 학습 (생육/환경/일사량/판매 등)
RDA_DATA_DIR = DATA_DIR / "농진청 표준"         # 환경관리 탭 농진청 표준 xlsx
SAMPLE_DATA_DIR = DATA_DIR / "test"             # 데모 업로드 파일
GEO_DATA_PATH = DATA_DIR / "korea_admin_district.json"
