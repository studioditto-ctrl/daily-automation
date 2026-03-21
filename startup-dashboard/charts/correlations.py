"""투자자 분석 차트"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from charts._theme import apply, CAT_COLORS, fmt_krw


def investor_bar(investor_df: pd.DataFrame, top_n: int = 15, total_companies: int = None):
    if investor_df.empty:
        return None
    data = investor_df.head(top_n).sort_values("참여 기업 수")

    if total_companies:
        data = data.copy()
        data["비율(%)"] = (data["참여 기업 수"] / total_companies * 100).round(1)
        data["라벨"] = data.apply(
            lambda r: f"{int(r['참여 기업 수'])}개 ({r['비율(%)']:.1f}%)", axis=1
        )
    else:
        data["라벨"] = data["참여 기업 수"].astype(int).astype(str) + "개"

    fig = go.Figure(go.Bar(
        y=data["투자자"],
        x=data["참여 기업 수"],
        orientation="h",
        text=data["라벨"],
        textposition="outside",
        marker=dict(
            color=data["참여 기업 수"],
            colorscale=[[0, "#fff7ed"], [1, "#c2410c"]],
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    apply(fig, {
        "title": f"주요 투자자 참여 기업 수 (상위 {top_n}명)",
        "xaxis": dict(title="참여 기업 수 (개)", showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        "yaxis": dict(showgrid=False),
        "height": max(380, top_n * 32),
    })
    return fig


def employee_invest_scatter(df: pd.DataFrame):
    sub = df[["기업명", "고용인원(명)", "총 투자 유치 금액", "대분야", "최근 투자 단계"]].dropna(
        subset=["고용인원(명)", "총 투자 유치 금액"]
    )
    if sub.empty:
        return None
    sub = sub.copy()
    sub["금액라벨"] = sub["총 투자 유치 금액"].apply(fmt_krw)
    sub["1인당투자"] = sub.apply(
        lambda r: fmt_krw(r["총 투자 유치 금액"] / r["고용인원(명)"])
        if r["고용인원(명)"] > 0 else "N/A", axis=1
    )

    fig = px.scatter(
        sub,
        x="고용인원(명)", y="총 투자 유치 금액",
        color="최근 투자 단계",
        hover_name="기업명",
        size="고용인원(명)", size_max=40,
        color_discrete_sequence=CAT_COLORS,
        labels={"고용인원(명)": "고용 인원 (명)", "총 투자 유치 금액": "총 투자 금액 (원)"},
        custom_data=["금액라벨", "1인당투자", "대분야"],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "고용: %{x}명 | 총 투자: %{customdata[0]}<br>"
            "1인당 투자: %{customdata[1]}<br>"
            "분야: %{customdata[2]}<extra></extra>"
        )
    )
    apply(fig, {"title": "고용 인원 vs 총 투자 금액 (1인당 투자 포함)"})
    return fig
