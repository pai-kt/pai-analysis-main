#!/usr/bin/env python3
"""실행 화면 캡처 + 사용 설명서 PDF 생성."""
from __future__ import annotations

import time
from pathlib import Path

from fpdf import FPDF
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "manual_assets"
PDF_PATH = ROOT / "docs" / "의사결정지원시스템_사용설명서.pdf"
FONT_PATH = ROOT / "fonts" / "NanumGothic.ttf"
APP_URL = "http://localhost:8510"
SECURITY_KEY = "abcd"

TAB_LABELS = ["1 데이터", "2 현황", "3 환경관리", "4 예측"]


def wait_for_streamlit(page, timeout_ms: int = 60000):
    page.goto(APP_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_selector('[data-testid="stApp"]', timeout=timeout_ms)


def click_tab(page, index: int):
    tabs = page.locator('[data-testid="stTabs"] [data-baseweb="tab-list"] button[data-baseweb="tab"]')
    tabs.nth(index).click()
    time.sleep(1.2)


def setup_demo_data(page):
    """보안키로 데모 데이터 로드 후 분석 실행."""
    page.get_by_text("보안키 사용", exact=True).click()
    time.sleep(2.0)

    key_input = page.locator('input[type="password"]').first
    key_input.wait_for(state="visible", timeout=15000)
    key_input.fill(SECURITY_KEY)
    key_input.press("Tab")
    time.sleep(3.0)

    btn = page.get_by_role("button", name="분석 결과 보기")
    btn.wait_for(state="visible", timeout=15000)
    for _ in range(10):
        if not btn.is_disabled():
            break
        time.sleep(1.0)
    if btn.is_disabled():
        raise RuntimeError("분석 버튼이 비활성화 상태입니다. 보안키 또는 샘플 데이터를 확인하세요.")
    btn.click()
    time.sleep(4.0)


def capture_screenshots() -> dict[str, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shots: dict[str, Path] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, locale="ko-KR")
        page = context.new_page()

        wait_for_streamlit(page)
        setup_demo_data(page)

        # 탭 2(현황)로 자동 이동될 수 있음 — 데이터 탭부터 순서대로 캡처
        for i, label in enumerate(TAB_LABELS):
            click_tab(page, i)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            fname = f"tab{i + 1}_{label.split()[1]}.png"
            path = OUT_DIR / fname
            page.screenshot(path=str(path), full_page=(i >= 1))
            shots[label] = path

        # 데이터 탭 — 매핑 확인 영역 (접힌 상태 + 펼친 상태)
        click_tab(page, 0)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)
        mapping_path = OUT_DIR / "tab1_mapping.png"
        expander = page.locator('[data-testid="stExpander"]').first
        if expander.count():
            expander.locator("summary").click()
            time.sleep(0.6)
        page.screenshot(path=str(mapping_path), full_page=False)
        shots["매핑 확인"] = mapping_path

        browser.close()

    return shots


class ManualPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Nanum", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"- {self.page_no()} -", align="C")


def build_pdf(shots: dict[str, Path]) -> Path:
    pdf = ManualPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Nanum", "", str(FONT_PATH))
    pdf.add_font("Nanum", "B", str(FONT_PATH))

    def section_title(title: str):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Nanum", "B", 16)
        pdf.set_text_color(36, 50, 64)
        pdf.ln(2)
        pdf.multi_cell(0, 9, title)
        pdf.ln(2)

    def body(text: str, size: int = 11):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Nanum", "", size)
        pdf.set_text_color(60, 70, 80)
        pdf.multi_cell(0, 6.5, text)
        pdf.ln(1.5)

    def bullet(text: str):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Nanum", "", 10.5)
        pdf.set_text_color(60, 70, 80)
        pdf.multi_cell(0, 6, f"  - {text}")

    def add_image(path: Path, caption: str, max_h: float = 200):
        if not path.exists():
            return
        pdf.ln(2)
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.image(str(path), x=pdf.l_margin, w=usable_w)
        pdf.ln(2)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Nanum", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5, caption)
        pdf.ln(3)

    # 표지
    pdf.add_page()
    pdf.set_font("Nanum", "B", 24)
    pdf.set_text_color(36, 50, 64)
    pdf.ln(35)
    pdf.cell(0, 12, "의사결정지원시스템 (A-DIMS)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Nanum", "", 14)
    pdf.set_text_color(78, 121, 167)
    pdf.cell(0, 10, "시설원예 생육·환경 데이터 기반 분석·예측", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Nanum", "B", 18)
    pdf.set_text_color(36, 50, 64)
    pdf.cell(0, 10, "사용 설명서", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Nanum", "", 11)
    pdf.set_text_color(90, 100, 110)
    pdf.multi_cell(
        0,
        7,
        "본 문서는 `streamlit run app.py` 실행 시 나타나는 화면을 기준으로 "
        "시스템 구성, 데이터 입력, 분석 결과 확인 방법을 안내합니다.",
        align="C",
    )

    # 1. 개요
    pdf.add_page()
    section_title("1. 시스템 개요")
    body(
        "의사결정지원시스템(A-DIMS)은 시설원예(토마토 등) 농가의 환경센서 데이터와 "
        "생육·수확 조사 데이터를 결합하여, 현재 상태 진단, 환경관리 분석, "
        "수확·착과 전망을 제공하는 웹 대시보드입니다."
    )
    body("주요 기능:")
    bullet("환경·생육 데이터 업로드 및 자동 컬럼 매핑")
    bullet("생육 진척·환경 상태 KPI 및 조치 권고")
    bullet("생육·수확 시계열 차트 (실측 vs 참조 표준)")
    bullet("농진청(RDA) 표준 환경·생산량 조회")
    bullet("RandomForest 기반 수확·착과·초장 추정")
    pdf.ln(3)
    body("화면은 상단 4개 탭으로 구성됩니다.")
    bullet("1 데이터 — 작물 선택, 파일 업로드, 분석 실행")
    bullet("2 현황 — 오늘의 생육·환경 상태, 조치 항목")
    bullet("3 환경관리 — RDA 표준 조회, 환경 상세")
    bullet("4 예측 — 모델 추정")

    # 2. 실행 방법
    pdf.add_page()
    section_title("2. 실행 방법")
    body("터미널에서 프로젝트 폴더로 이동한 뒤 아래 명령을 실행합니다.")
    pdf.set_font("Nanum", "", 10)
    pdf.set_fill_color(247, 248, 250)
    pdf.multi_cell(0, 7, "  cd pai-analysis-main\n  source .venv/bin/activate   # 가상환경 사용 시\n  streamlit run app.py", fill=True)
    pdf.ln(3)
    body("브라우저가 자동으로 열리며, 기본 주소는 http://localhost:8501 입니다.")
    body("종료하려면 터미널에서 Ctrl+C 를 누릅니다.")

    # 3. 데이터 입력
    pdf.add_page()
    section_title("3. 데이터 입력 (탭 1 · 데이터)")
    body("분석을 시작하려면 환경센서 파일과 수확·생육 파일이 모두 필요합니다.")
    pdf.ln(1)
    body("입력 방식 (둘 중 하나 선택):", size=12)
    bullet("보안키 사용 — 데모용 샘플 데이터로 바로 분석 (데모 키: abcd)")
    bullet("파일 업로드 — CSV 또는 Excel(xlsx) 파일 2개 업로드")
    pdf.ln(2)
    body("환경센서 파일 필수 컬럼: 측정일자, 온도, 습도, CO₂, 외부누적일사량")
    body("수확·생육 파일 필수 컬럼: 조사일자, 수확수, 착과수, 생육 측정값(초장 등)")
    pdf.ln(2)
    body("파일 업로드 후 「매핑 데이터 확인 · 자동 인식됨」에서 컬럼이 올바른지 확인합니다. "
         "자동 인식이 맞지 않으면 「컬럼이 맞지 않으면 직접 지정」을 체크하여 수동 매핑합니다.")
    body("「평균 계산 기간(주)」은 환경 변수를 주 단위로 집계하는 기간(1~7주)입니다. "
         "기본값 7주를 권장합니다.")
    body("모든 설정이 완료되면 「분석 결과 보기 →」 버튼을 클릭합니다. "
         "분석이 완료되면 자동으로 「2 현황」 탭으로 이동합니다.")

    if "1 데이터" in shots:
        add_image(shots["1 데이터"], "그림 1. 데이터 탭 — 작물 선택, 파일 업로드, 분석 실행")
    if "매핑 확인" in shots:
        add_image(shots["매핑 확인"], "그림 2. 매핑 데이터 확인 (자동 인식된 컬럼)")

    # 4. 현황
    pdf.add_page()
    section_title("4. 현황 확인 (탭 2 · 현황)")
    body("업로드한 데이터를 기준으로 현재 생육·환경 상태를 한눈에 보여줍니다.")
    bullet("생육 진척 카드 — 표준 곡선 대비 초장·생육 상태 (정상/주의/지연)")
    bullet("환경 상태 카드 — 최근 7일 센서 평균 기준 위험·주의 항목")
    bullet("누적 수확수·착과수 — 조사일자별 합산 누계")
    bullet("생육·수확 시계열 차트 — 실선(내 농가) vs 회색 점선(참조 표준)")
    bullet("오늘 해야 할 일 — 환경 KPI 기반 우선 조치 권고")
    pdf.ln(2)
    body("상단 알림(트리아지)은 즉시 확인이 필요한 환경 이슈를 강조 표시합니다.")

    if "2 현황" in shots:
        add_image(shots["2 현황"], "그림 3. 현황 탭 — 생육·환경 KPI 및 조치 권고", max_h=999)

    # 5. 환경관리
    pdf.add_page()
    section_title("5. 환경관리 (탭 3 · 환경관리)")
    body("농진청(RDA) 표준 데이터 조회와 환경 상세 기능을 제공합니다.")
    bullet("생육단계 바 — 정식·영양생장 → 개화기 → 착과기 → 비대·수확기")
    bullet("일사량별 최적환경 — 누적일사량·외기기온 입력 → RDA 권장 환경 설정 조회")
    bullet("생육상태별 최적생산량 — 생육단계·외기기온 기준 표준 생산량 조회")
    pdf.ln(2)
    body("외기기온은 GPS 자동 조회 또는 시·도·군·구 수동 선택으로 입력할 수 있습니다.")

    if "3 환경관리" in shots:
        add_image(shots["3 환경관리"], "그림 4. 환경관리 탭 — RDA 표준 조회", max_h=999)

    # 6. 예측
    pdf.add_page()
    section_title("6. 예측 (탭 4 · 예측)")
    body("앞으로의 수확·생육 전망과 사전 학습 모델 추정치를 확인합니다.")
    body("상단 3개 카드 (참고 전망):", size=12)
    bullet("예상 수확 시기 — 표준 대비 지연 일수")
    bullet("생육 지연 전망 — 환경 관리 시 단축 가능 일수")
    bullet("예상 착과수 — 현재 누계 기준")
    pdf.ln(1)
    body("하단 RandomForest 블록 (모델 추정):", size=12)
    bullet("모델 추정 · 수확수 / 착과수 / 생육 지연(초장)")
    bullet("사전 학습 모델(models/)을 불러와 최근 조사 1행 환경으로 추정")

    if "4 예측" in shots:
        add_image(shots["4 예측"], "그림 5. 예측 탭 — 전망 카드 및 모델 추정", max_h=999)

    # 7. FAQ
    pdf.add_page()
    section_title("7. 자주 묻는 질문")
    body("Q. 분석 버튼이 비활성화되어 있습니다.", size=12)
    body("A. 환경센서·수확·생육 파일을 모두 업로드했는지, 또는 올바른 보안키를 입력했는지 확인하세요.")
    pdf.ln(2)
    body("Q. 컬럼이 자동 인식되지 않습니다.", size=12)
    body("A. 「컬럼이 맞지 않으면 직접 지정」을 체크하고 각 필드를 수동으로 매핑하세요.")
    pdf.ln(2)
    body("Q. 모델 예측이 표시되지 않습니다.", size=12)
    body("A. `python train_reference_models.py` 로 models/ 폴더에 사전 학습 모델을 생성했는지 확인하세요.")
    pdf.ln(2)
    body("Q. 한글이 깨집니다.", size=12)
    body("A. fonts/NanumGothic.ttf 파일이 프로젝트에 포함되어 있는지 확인하세요.")

    pdf.ln(5)
    pdf.set_font("Nanum", "", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(
        0,
        5,
        "본 문서는 A-DIMS(의사결정지원시스템) v0.04 인터페이스 기준으로 작성되었습니다.\n"
        "분석 결과는 참고용이며, 현장 관찰과 전문가 판단을 우선하시기 바랍니다.",
        align="C",
    )

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(PDF_PATH))
    return PDF_PATH


def main():
    print("Streamlit 화면 캡처 중…")
    shots = capture_screenshots()
    for k, v in shots.items():
        print(f"  ✓ {k}: {v}")

    print("PDF 생성 중…")
    path = build_pdf(shots)
    print(f"완료: {path}")


if __name__ == "__main__":
    main()
