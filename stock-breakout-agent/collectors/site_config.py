"""
RS 데이터 수집 사이트 설정 — StockEasy (intellio.kr)

사이트 구조:
  - 로그인: https://www.intellio.kr/login (Google OAuth)
  - RS 랭킹: https://stockeasy.intellio.kr/rs-rank?tab=integrated_rs
  - Next.js 기반 SPA, 테이블 데이터는 JS 렌더링 후 로드됨
"""
import os

# ── 사이트 URL ──
SITE_URL    = os.getenv("SITE_URL",    "https://stockeasy.intellio.kr/")
LOGIN_URL   = os.getenv("LOGIN_URL",   "https://www.intellio.kr/login")
RS_RANK_URL = os.getenv("RS_RANK_URL", "https://stockeasy.intellio.kr/rs-rank?tab=integrated_rs")

# ── 로그인 폼 셀렉터 (intellio.kr 로그인 페이지) ──
# Google 로그인 버튼 (텍스트 기반 셀렉터 사용)
GOOGLE_LOGIN_BTN = "button:has-text('Google로 로그인')"

# Google OAuth 페이지 셀렉터
GOOGLE_EMAIL_INPUT    = "input[type='email']"
GOOGLE_EMAIL_NEXT     = "button:has-text('다음'), #identifierNext"
GOOGLE_PASSWORD_INPUT = "input[type='password']"
GOOGLE_PASSWORD_NEXT  = "button:has-text('다음'), #passwordNext"

# 로그인 성공 확인 — StockEasy 메인으로 리디렉션 완료 여부
LOGIN_SUCCESS_URL_PATTERN = "stockeasy.intellio.kr"

# ── RS 랭킹 테이블 셀렉터 ──
# Next.js SPA이므로 데이터 로드 완료까지 대기 필요
RS_TABLE_WAIT_SELECTOR = "table, [role='grid'], tbody tr"
RS_ROW_SELECTOR        = "tbody tr"

# 열 자동 감지 활성화 (헤더 텍스트로 열 인덱스 자동 매핑)
AUTO_DETECT_COLUMNS = True

# 열 헤더 매핑 (사이트 헤더 텍스트 → 내부 필드명)
# 실제 사이트 헤더와 다르면 여기를 수정
COLUMN_HEADER_MAP = {
    "종목코드": "code",
    "티커":     "code",
    "코드":     "code",
    "종목명":   "name",
    "종목":     "name",
    "이름":     "name",
    "RS":       "rs_score",
    "RS점수":   "rs_score",
    "RS 점수":  "rs_score",
    "상대강도": "rs_score",
    "통합RS":   "rs_score",
    "섹터":     "sector",
    "업종":     "sector",
    "시가총액": "market_cap",
}

# ── 페이지네이션 ──
PAGINATION_ENABLED = os.getenv("PAGINATION_ENABLED", "false").lower() == "true"
NEXT_PAGE_SELECTOR = "button[aria-label='다음 페이지'], button:has-text('다음')"
MAX_PAGES          = int(os.getenv("MAX_PAGES", "5"))

# ── 타임아웃 (밀리초) ──
PAGE_LOAD_TIMEOUT   = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))
ACTION_TIMEOUT      = int(os.getenv("ACTION_TIMEOUT", "15000"))
TABLE_WAIT_TIMEOUT  = int(os.getenv("TABLE_WAIT_TIMEOUT", "20000"))
