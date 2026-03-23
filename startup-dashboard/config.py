import os

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# Anthropic API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# THE VC 컬럼명 → 내부 역할 매핑 (한국어 고정 컬럼)
COLUMN_MAP = {
    "기업명": "company",
    "대표 제품/서비스명": "product_name",
    "대표 제품/서비스 설명": "product_desc",
    "기술": "tech_type",
    "대분야": "major_field",
    "소분야": "minor_field",
    "재무 기준년도": "fiscal_year",
    "매출": "revenue",
    "순이익": "net_income",
    "고용인원(명)": "employees",
    "총 투자 유치 횟수": "invest_rounds",
    "총 투자 유치 금액": "invest_total",
    "최근 투자 단계": "invest_stage",
    "최근 투자 유치일": "invest_date",
    "주요 투자자": "investors",
    "기업 이메일": "email",
    "웹사이트 링크": "website",
    "더브이씨 프로필 링크": "thevc_link",
}

# 역방향: 내부 역할 → 컬럼명
ROLE_TO_COL = {v: k for k, v in COLUMN_MAP.items()}

# 투자 단계 정렬 순서
STAGE_ORDER = ["Seed", "Pre-A", "Series A", "Series B", "Series C", "Growth", "IPO", "해당 없음"]

# 결측 표현 (문자열)
NA_STRINGS = {"알 수 없음", "해당 없음", "nan", "None", "", "-", "N/A"}
