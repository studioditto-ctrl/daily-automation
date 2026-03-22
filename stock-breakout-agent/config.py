import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# RS 계산 기준 (pykrx 자체 계산 — 로그인 불필요)
RS_MARKETS = ["KOSPI", "KOSDAQ"]  # 대상 시장

# 1차 후보군 필터 기준
RS_THRESHOLD = int(os.getenv("RS_THRESHOLD", "80"))        # RS 최소 점수
MAX_FIRST_CANDIDATES = int(os.getenv("MAX_FIRST_CANDIDATES", "50"))   # 1차 최대 종목 수
MAX_SECOND_CANDIDATES = int(os.getenv("MAX_SECOND_CANDIDATES", "20"))  # 2차 최대 종목 수

# 차트 분석
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "120"))      # OHLCV 조회 기간 (영업일)
VOLUME_RATIO_MIN = float(os.getenv("VOLUME_RATIO_MIN", "1.5"))  # 거래량 배수 최소치

# 웹 대시보드
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

# 스토리지
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "storage", "reports")
