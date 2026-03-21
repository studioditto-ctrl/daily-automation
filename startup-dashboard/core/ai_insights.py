"""
Claude API 인사이트 생성 모듈 - THE VC 스타트업 데이터 특화
"""
import anthropic
import pandas as pd

from config import CLAUDE_MODEL


class StartupInsightAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call(self, prompt: str, max_tokens: int = 2500) -> str:
        resp = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()

    def generate_full_report(self, context: dict) -> str:
        n = context.get("n_companies", 0)
        field_md = _df_to_md(context.get("field_df"))
        tech_md = _df_to_md(context.get("tech_df"))
        stage_md = _df_to_md(context.get("stage_df"))
        investor_md = _df_to_md(context.get("investor_df"), max_rows=20)
        stats_md = _df_to_md(context.get("stats_df"))
        company_list = context.get("company_list", "")

        prompt = f"""당신은 한국 스타트업 생태계 전문 투자 애널리스트입니다.
아래는 THE VC 8기 코호트 스타트업 {n}개사의 데이터입니다.

=== 기업 목록 ===
{company_list}

=== 산업 분야별 분포 ===
{field_md}

=== 기술 분류별 분포 ===
{tech_md}

=== 투자 단계별 분포 ===
{stage_md}

=== 주요 투자자 참여 현황 ===
{investor_md}

=== 재무/운영 통계 ===
{stats_md}

위 데이터를 바탕으로 아래 구조로 심층 분석을 작성하세요.
반드시 실제 수치와 기업명을 인용하고, 한국 스타트업 생태계 맥락에서 해석하세요:

## 코호트 전체 개요
[{n}개사의 전반적 특성, 단계, 산업 분포 요약]

## 산업 및 기술 트렌드
[지배적인 분야, 주목할 틈새, AI 기술 집중도 분석]

## 투자 생태계 분석
[투자 단계 분포, 팁스 등 주요 투자자 역할, 투자 금액 패턴]

## 재무 및 성장 지표
[매출·순이익 현황, 고용 규모, 성장 잠재력]

## 주목할 기업
[투자 금액, 기술, 성장성 측면에서 두드러진 기업 3~5개]

## 투자자 관점 시사점
[이 코호트에서 발견되는 투자 기회와 리스크 요인]
"""
        return self._call(prompt)


def build_context(
    df: pd.DataFrame,
    field_df: pd.DataFrame,
    tech_df: pd.DataFrame,
    stage_df: pd.DataFrame,
    investor_df: pd.DataFrame,
    stats_df: pd.DataFrame,
) -> dict:
    company_list = "\n".join(
        f"- {row['기업명']}: {row.get('대표 제품/서비스명', '')} ({row.get('대분야', '')} / {row.get('기술', '')})"
        for _, row in df.iterrows()
        if pd.notna(row.get("기업명"))
    )
    return {
        "n_companies": len(df),
        "company_list": company_list,
        "field_df": field_df,
        "tech_df": tech_df,
        "stage_df": stage_df,
        "investor_df": investor_df,
        "stats_df": stats_df,
    }


def _df_to_md(df, max_rows: int = 20) -> str:
    if df is None or (hasattr(df, "empty") and df.empty):
        return "데이터 없음"
    try:
        subset = df.head(max_rows).copy()
        num_cols = subset.select_dtypes(include="number").columns
        subset[num_cols] = subset[num_cols].round(0)
        return subset.to_markdown(index=False)
    except Exception:
        return str(df.head(max_rows))
