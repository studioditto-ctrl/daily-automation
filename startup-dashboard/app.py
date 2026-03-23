"""
THE VC 스타트업 DB 통계 분석 대쉬보드
실행: streamlit run app.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

from config import ANTHROPIC_API_KEY
from core.loader import get_investor_counts
from core.analyzer import (
    kpi_summary, field_breakdown, minor_field_breakdown,
    tech_breakdown, stage_breakdown, investment_year_trend,
    financial_stats, stage_field_cross, apply_filters,
)
from charts.breakdowns import (
    major_field_treemap, major_field_bar, minor_field_bar,
    tech_pie, tech_bar, stage_bar, stage_pie, stage_field_heatmap,
)
from charts.distributions import (
    invest_histogram, revenue_bar, net_income_bar,
    employee_bar, invest_vs_revenue_scatter, rounds_vs_amount_scatter,
)
from charts.timeseries import dual_trend, invest_year_bar
from charts.correlations import investor_bar, employee_invest_scatter
from ui.upload import render_upload_section
from ui.sidebar import render_sidebar
from ui.summary_cards import render_kpi_cards
from ui.insights_panel import render_insights_panel

# ── 페이지 설정 ───────────────────────────────
st.set_page_config(
    page_title="THE VC 스타트업 분석",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 전문 금융 CSS ──────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
.stApp { background: #f8fafc; }

/* 메인 헤더 */
h1 { font-size: 1.6rem !important; font-weight: 700 !important; color: #0f172a !important; letter-spacing: -0.3px; }
h2 { font-size: 1.15rem !important; font-weight: 600 !important; color: #1e3a5f !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; color: #334155 !important; }

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.85rem;
    color: #64748b;
    padding: 6px 16px;
    border: none;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #1e3a5f !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #1e3a5f;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"],
[data-testid="stSidebar"] .stSlider [data-testid="stSlider"] {
    background: #1e3a5f;
    border-color: #334d6a;
}
[data-testid="stSidebar"] input {
    background: #243f6e !important;
    border: 1px solid #2d5080 !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stSidebar"] hr {
    border-color: #2d5080 !important;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #93c5fd !important;
}

/* 데이터프레임 */
.stDataFrame { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(15,23,42,0.06); }

/* divider */
hr { border-color: #e2e8f0 !important; }

/* 캡션 */
.stCaption { color: #64748b !important; font-size: 0.78rem !important; }

/* info / warning */
.stAlert { border-radius: 8px !important; }

/* selectbox, slider */
.stSelectbox [data-baseweb="select"] > div,
.stSlider [data-testid="stSliderTrack"] { border-radius: 6px; }

/* checkbox */
.stCheckbox span { font-size: 0.875rem; color: #334155; }
</style>
""", unsafe_allow_html=True)

if "ai_insights" not in st.session_state:
    st.session_state["ai_insights"] = {}
if "ready" not in st.session_state:
    st.session_state["ready"] = False

# ── API Key ───────────────────────────────────
with st.sidebar:
    st.subheader("설정")
    api_key = st.text_input(
        "Anthropic API Key",
        value=ANTHROPIC_API_KEY,
        type="password",
        placeholder="sk-ant-...",
    )
    st.divider()

# ── 헤더 & 업로드 ─────────────────────────────
st.title("THE VC 스타트업 DB 분석 대쉬보드")
st.caption("THE VC에서 내려받은 엑셀 파일을 업로드하면 심층 통계 분석을 제공합니다.")

ready = render_upload_section()
if not ready:
    st.stop()

# ── 데이터 로드 & 필터 ────────────────────────
df: pd.DataFrame = st.session_state["clean_df"]
filters = render_sidebar(df)
fdf = apply_filters(df, filters) if filters else df

st.divider()

# ── KPI 카드 ──────────────────────────────────
kpi = kpi_summary(fdf)
render_kpi_cards(kpi, total_df_len=len(df))
if filters:
    st.caption(f"필터 적용: {len(fdf)}개 기업 (전체 {len(df)}개 중)")

st.divider()

# ── 분석 데이터 계산 ──────────────────────────
field_df   = field_breakdown(fdf)
minor_df   = minor_field_breakdown(fdf)
tech_df    = tech_breakdown(fdf)
stage_df   = stage_breakdown(fdf)
ts_df      = investment_year_trend(fdf)
stats_df   = financial_stats(fdf)
cross_df   = stage_field_cross(fdf)
investor_df = get_investor_counts(fdf["주요 투자자"] if "주요 투자자" in fdf.columns else pd.Series(dtype=str))

# ── 탭 ───────────────────────────────────────
tab_overview, tab_industry, tab_invest, tab_finance, tab_investors, tab_ai = st.tabs([
    "📊 개요",
    "🏭 산업/기술",
    "💰 투자 분석",
    "📈 재무 현황",
    "🤝 투자자",
    "🤖 AI 인사이트",
])

# ── 탭1: 개요 ─────────────────────────────────
with tab_overview:
    col1, col2 = st.columns(2)
    with col1:
        fig = major_field_treemap(field_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = tech_pie(tech_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    fig = stage_field_heatmap(cross_df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("전체 기업 목록")
    display_cols = [c for c in [
        "기업명", "대표 제품/서비스명", "대분야", "소분야", "기술",
        "최근 투자 단계", "총 투자 유치 금액", "고용인원(명)", "더브이씨 프로필 링크"
    ] if c in fdf.columns]
    st.dataframe(
        fdf[display_cols].reset_index(drop=True),
        use_container_width=True,
        column_config={
            "더브이씨 프로필 링크": st.column_config.LinkColumn("THE VC 프로필"),
            "총 투자 유치 금액": st.column_config.NumberColumn("투자 유치 금액(원)", format="%d"),
        }
    )

# ── 탭2: 산업/기술 ────────────────────────────
with tab_industry:
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("대분야 지표", ["기업수", "총 투자 유치 금액"], key="field_metric")
        fig = major_field_bar(field_df, metric=metric)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = minor_field_bar(minor_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = tech_bar(tech_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("기술 분류 상세")
        st.dataframe(tech_df, use_container_width=True)

    st.subheader("대분야 상세 데이터")
    st.dataframe(field_df, use_container_width=True)

# ── 탭3: 투자 분석 ────────────────────────────
with tab_invest:
    col1, col2 = st.columns(2)
    with col1:
        fig = stage_pie(stage_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        metric = st.selectbox("스테이지 지표", ["기업수", "총 투자 유치 금액", "중앙 투자 금액"], key="stage_metric")
        fig = stage_bar(stage_df, metric=metric)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    log_toggle = st.checkbox("로그 스케일", value=True, key="invest_log")
    fig = invest_histogram(fdf, log_scale=log_toggle)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = rounds_vs_amount_scatter(fdf)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if not ts_df.empty:
            fig = dual_trend(ts_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("투자 단계별 상세")
    st.dataframe(stage_df, use_container_width=True)

# ── 탭4: 재무 현황 ────────────────────────────
with tab_finance:
    if not stats_df.empty:
        st.subheader("재무/운영 기술통계")
        st.dataframe(
            stats_df.style.format("{:,.0f}", na_rep="N/A"),
            use_container_width=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        fig = revenue_bar(fdf)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("매출 데이터 없음")
    with col2:
        fig = net_income_bar(fdf)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("순이익 데이터 없음")

    col1, col2 = st.columns(2)
    with col1:
        fig = employee_bar(fdf)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = invest_vs_revenue_scatter(fdf)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("투자금액·매출 동시 보유 기업이 부족합니다.")

# ── 탭5: 투자자 ───────────────────────────────
with tab_investors:
    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("상위 투자자 수", 5, 30, 15, key="inv_top")
        fig = investor_bar(investor_df, top_n=top_n)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("투자자 전체 목록")
        st.dataframe(investor_df, use_container_width=True, height=500)

    fig = employee_invest_scatter(fdf)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("기업별 주요 투자자")
    inv_cols = [c for c in ["기업명", "최근 투자 단계", "총 투자 유치 금액", "총 투자 유치 횟수", "주요 투자자"] if c in fdf.columns]
    st.dataframe(fdf[inv_cols].dropna(subset=["주요 투자자"]), use_container_width=True)

# ── 탭6: AI 인사이트 ──────────────────────────
with tab_ai:
    render_insights_panel(fdf, field_df, tech_df, stage_df, investor_df, stats_df, api_key)
