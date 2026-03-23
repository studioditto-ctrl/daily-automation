"""
THE VC 스타트업 데이터 통계 분석 모듈
"""
import numpy as np
import pandas as pd

from config import STAGE_ORDER


def kpi_summary(df: pd.DataFrame) -> dict:
    """대쉬보드 KPI 카드 지표."""
    total = len(df)
    has_invest = df["총 투자 유치 금액"].dropna()
    has_revenue = df["매출"].dropna()
    has_emp = df["고용인원(명)"].dropna()

    return {
        "total_companies": total,
        "total_invest": has_invest.sum() if not has_invest.empty else None,
        "median_invest": has_invest.median() if not has_invest.empty else None,
        "avg_revenue": has_revenue.mean() if not has_revenue.empty else None,
        "total_employees": int(has_emp.sum()) if not has_emp.empty else None,
        "n_stages": df["최근 투자 단계"].nunique(),
        "n_major_fields": df["대분야"].nunique(),
        "n_tech_types": df["기술"].nunique(),
    }


def field_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """대분야별 기업수, 총/중앙 투자금액."""
    agg = {"기업수": ("대분야", "count")}
    if "총 투자 유치 금액" in df.columns:
        agg["총 투자 유치 금액"] = ("총 투자 유치 금액", "sum")
        agg["중앙 투자 금액"] = ("총 투자 유치 금액", "median")
    result = df.groupby("대분야").agg(**agg).reset_index()
    return result.sort_values("기업수", ascending=False).reset_index(drop=True)


def minor_field_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """소분야별 기업수."""
    result = df.groupby("소분야").agg(기업수=("소분야", "count")).reset_index()
    return result.sort_values("기업수", ascending=False).reset_index(drop=True)


def tech_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """기술 분류별 기업수, 투자금액."""
    agg = {"기업수": ("기술", "count")}
    if "총 투자 유치 금액" in df.columns:
        agg["총 투자 유치 금액"] = ("총 투자 유치 금액", "sum")
    result = df.groupby("기술").agg(**agg).reset_index()
    return result.sort_values("기업수", ascending=False).reset_index(drop=True)


def stage_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """투자 단계별 기업수, 총/중앙 투자금액."""
    agg = {"기업수": ("최근 투자 단계", "count")}
    if "총 투자 유치 금액" in df.columns:
        agg["총 투자 유치 금액"] = ("총 투자 유치 금액", "sum")
        agg["중앙 투자 금액"] = ("총 투자 유치 금액", "median")
    result = df.groupby("최근 투자 단계").agg(**agg).reset_index()
    result["_order"] = result["최근 투자 단계"].map(
        lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 999
    )
    return result.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def investment_year_trend(df: pd.DataFrame) -> pd.DataFrame:
    """최근 투자 유치 연도별 기업수, 투자금액."""
    if "투자연도" not in df.columns:
        return pd.DataFrame()
    sub = df.dropna(subset=["투자연도"]).copy()
    sub["투자연도"] = sub["투자연도"].astype(int)
    agg = {"기업수": ("투자연도", "count")}
    if "총 투자 유치 금액" in df.columns:
        agg["총 투자 유치 금액"] = ("총 투자 유치 금액", "sum")
    result = sub.groupby("투자연도").agg(**agg).reset_index()
    return result.sort_values("투자연도").reset_index(drop=True)


def financial_stats(df: pd.DataFrame) -> pd.DataFrame:
    """매출, 순이익, 투자금액, 고용인원 기술통계."""
    cols = ["매출", "순이익", "총 투자 유치 금액", "고용인원(명)", "총 투자 유치 횟수"]
    valid_cols = [c for c in cols if c in df.columns and df[c].notna().any()]
    if not valid_cols:
        return pd.DataFrame()

    records = []
    for col in valid_cols:
        s = df[col].dropna()
        records.append({
            "지표": col,
            "데이터수": int(s.count()),
            "합계": s.sum(),
            "평균": s.mean(),
            "중앙값": s.median(),
            "최솟값": s.min(),
            "최댓값": s.max(),
            "표준편차": s.std(),
        })
    return pd.DataFrame(records).set_index("지표")


def stage_field_cross(df: pd.DataFrame) -> pd.DataFrame:
    """투자 단계 × 대분야 교차표."""
    if "최근 투자 단계" not in df.columns or "대분야" not in df.columns:
        return pd.DataFrame()
    ct = pd.crosstab(df["대분야"], df["최근 투자 단계"])
    # 단계 순서 정렬
    ordered_cols = [c for c in STAGE_ORDER if c in ct.columns]
    other_cols = [c for c in ct.columns if c not in STAGE_ORDER]
    return ct[ordered_cols + other_cols]


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """사이드바 필터 적용."""
    result = df.copy()

    if filters.get("major_fields"):
        result = result[result["대분야"].isin(filters["major_fields"])]
    if filters.get("stages"):
        result = result[result["최근 투자 단계"].isin(filters["stages"])]
    if filters.get("tech_types"):
        result = result[result["기술"].isin(filters["tech_types"])]
    if filters.get("min_invest") is not None:
        result = result[
            (result["총 투자 유치 금액"] >= filters["min_invest"]) |
            result["총 투자 유치 금액"].isna()
        ]

    return result.reset_index(drop=True)
