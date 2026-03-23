"""투자 연도 트렌드 차트"""
import plotly.graph_objects as go
import pandas as pd

from charts._theme import apply, BLUE_SEQ, fmt_krw


def dual_trend(ts_df: pd.DataFrame):
    if ts_df.empty or "투자연도" not in ts_df.columns:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ts_df["투자연도"],
        y=ts_df["기업수"],
        name="기업 수",
        marker=dict(color="#93c5fd", line=dict(width=0)),
        yaxis="y",
        text=ts_df["기업수"].astype(int),
        textposition="outside",
        hovertemplate="<b>%{x}년</b><br>기업 수: %{y}개<extra></extra>",
    ))

    if "총 투자 유치 금액" in ts_df.columns:
        ts_df = ts_df.copy()
        ts_df["금액라벨"] = ts_df["총 투자 유치 금액"].apply(fmt_krw)
        fig.add_trace(go.Scatter(
            x=ts_df["투자연도"],
            y=ts_df["총 투자 유치 금액"],
            name="총 투자 금액",
            mode="lines+markers",
            line=dict(color="#1d4ed8", width=2.5),
            marker=dict(size=7, color="#1d4ed8"),
            yaxis="y2",
            hovertemplate="<b>%{x}년</b><br>총 투자: %{customdata}<extra></extra>",
            customdata=ts_df["금액라벨"],
        ))

    apply(fig, {
        "title": "연도별 투자 유치 현황 (기업 수 & 총 금액)",
        "xaxis": dict(title="최근 투자 유치 연도", tickmode="linear", showgrid=False),
        "yaxis": dict(title="기업 수 (개)", showgrid=True, gridcolor="#f1f5f9"),
        "yaxis2": dict(title="총 투자 금액 (원)", overlaying="y", side="right", showgrid=False),
        "hovermode": "x unified",
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    })
    return fig


def invest_year_bar(ts_df: pd.DataFrame):
    if ts_df.empty or "투자연도" not in ts_df.columns:
        return None
    total = ts_df["기업수"].sum()
    ts_df = ts_df.copy()
    ts_df["라벨"] = ts_df["기업수"].apply(lambda v: f"{int(v)}개 ({v/total*100:.0f}%)")

    fig = go.Figure(go.Bar(
        x=ts_df["투자연도"],
        y=ts_df["기업수"],
        text=ts_df["라벨"],
        textposition="outside",
        marker=dict(
            color=ts_df["기업수"],
            colorscale=BLUE_SEQ,
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}년</b><br>%{text}<extra></extra>",
    ))
    apply(fig, {
        "title": "최근 투자 유치 연도별 기업 수 및 구성비",
        "xaxis": dict(title="연도", tickmode="linear", showgrid=False),
        "yaxis": dict(title="기업 수 (개)", showgrid=True, gridcolor="#f1f5f9"),
    })
    return fig
