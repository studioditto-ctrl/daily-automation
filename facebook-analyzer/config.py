#!/usr/bin/env python3
"""
Facebook Analyzer - 설정 모듈

필수 환경변수:
  ANTHROPIC_API_KEY  - Claude API 키 (https://console.anthropic.com)
  FB_PAGE_ID         - 대상 Facebook 페이지의 숫자 ID (예: "123456789012345")
  FB_ACCESS_TOKEN    - Facebook App Access Token (developers.facebook.com에서 발급)

선택 환경변수:
  FB_APP_ID          - Facebook App ID (토큰 갱신 시 필요)
  FB_APP_SECRET      - Facebook App Secret (토큰 갱신 시 필요)

환경변수 설정 방법 (Windows):
  setx ANTHROPIC_API_KEY "sk-ant-..."
  setx FB_PAGE_ID "123456789012345"
  setx FB_ACCESS_TOKEN "your-app-access-token"
  (설정 후 터미널 재시작 필요)
"""

import os
from pathlib import Path

# ── 경로 설정 ────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
REPORTS_DIR  = BASE_DIR / "reports"
DAILY_DIR    = REPORTS_DIR / "daily"
INSIGHTS_DIR = REPORTS_DIR / "insights"

MASTER_INSIGHTS_FILE = INSIGHTS_DIR / "master-insights.md"

# ── API 설정 ─────────────────────────────────────────────────────────────────
GRAPH_API_BASE = "https://graph.facebook.com/v18.0"
CLAUDE_MODEL   = "claude-sonnet-4-6"

# ── 크롤링 설정 ──────────────────────────────────────────────────────────────
MAX_POSTS_PER_REQUEST = 100   # Graph API 한 번에 최대 가져올 수 있는 게시물 수
MAX_HISTORY_PAGES     = 20    # --init 시 최대 페이지 수 (= 최대 2,000개 게시물)
REQUEST_DELAY_SEC     = 0.5   # 요청 간격 (Rate Limit 회피)

REQUIRED_ENV_VARS = ["ANTHROPIC_API_KEY", "FB_PAGE_ID", "FB_ACCESS_TOKEN"]


def validate_env() -> dict:
    """필수 환경변수 검증. 누락 시 즉시 종료."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise SystemExit(
            f"[ERROR] 다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}\n"
            f"        Windows에서 setx 명령어로 설정 후 터미널을 재시작하세요."
        )
    return {
        "anthropic_key": os.environ["ANTHROPIC_API_KEY"],
        "page_id":       os.environ["FB_PAGE_ID"],
        "access_token":  os.environ["FB_ACCESS_TOKEN"],
        "app_id":        os.environ.get("FB_APP_ID", ""),
        "app_secret":    os.environ.get("FB_APP_SECRET", ""),
    }


def ensure_dirs():
    """필요한 디렉터리를 생성한다."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
