import os
from dotenv import load_dotenv

load_dotenv()

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# RS 수집 사이트 — StockEasy (intellio.kr)
SITE_URL     = os.getenv("SITE_URL",  "https://stockeasy.intellio.kr/")
LOGIN_URL    = os.getenv("LOGIN_URL", "https://www.intellio.kr/login")
RS_RANK_URL  = os.getenv("RS_RANK_URL", "https://stockeasy.intellio.kr/rs-rank?tab=integrated_rs")

# Google OAuth 계정 정보 (.env에 설정)
GOOGLE_EMAIL    = os.getenv("GOOGLE_EMAIL", "")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD", "")

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
