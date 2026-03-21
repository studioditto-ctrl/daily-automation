"""재무/투자 금액 분포 차트"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from charts._theme import apply, BLUE_SEQ, CAT_COLORS, POS_COLOR, NEG_COLOR, fmt_krw


def invest_histogram(df: pd.DataFrame, log_scale: bool = True):
    data = df["총 투자 유치 금액"].dropna()
    if data.empty:
        return None
    fig = go.Figure(go.Histogram(
        x=data,
        nbinsx=20,
        marker=dict(color="#2563eb", line=dict(color="white", width=0.8)),
        hovertemplate="구간: %{x}<br>기업 수: %{y}개<extra></extra>",
    ))
    apply(fig, {
        "title": "총 투자 유치 금액 분포",
        "xaxis": dict(
            title="총 투자 유치 금액 (원)",
            type="log" if log_scale else "linear",
            showgrid=True, gridcolor="#f1f5f9",
        ),
        "yaxis": dict(title="기업 수 (개)", showgrid=True, gridcolor="#f1f5f9"),
        "bargap": 0.08,
    })
    return fig


def revenue_bar(df: pd.DataFrame):
    sub = df[["기업명", "매출"]].dropna().sort_values("매출", ascending=False)
    if sub.empty:
        return None
    sub["라벨"] = sub["매출"].apply(fmt_krw)
    fig = go.Figure(go.Bar(
        x=sub["기업명"],
        y=sub["매출"],
        text=sub["라벨"],
        textposition="outside",
        marker=dict(
            color=sub["매출"],
            colorscale=[[0, "#e0f2fe"], [1, "#0284c7"]],
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>매출: %{text}<extra></extra>",
    ))
    apply(fig, {
        "title": "기업별 연간 매출",
        "xaxis": dict(title="", tickangle=-35, showgrid=False),
        "yaxis": dict(title="매출 (원)", showgrid=True, gridcolor="#f1f5f9"),
    })
    return fig


def net_income_bar(df: pd.DataFrame):
    sub = df[["기업명", "순이익"]].dropna().sort_values("순이익")
    if sub.empty:
        return None
    colors = [NEG_COLOR if v < 0 else POS_COLOR for v in sub["순이익"]]
    sub["라벨"] = sub["순이익"].apply(fmt_krw)
    fig = go.Figure(go.Bar(
        x=sub["기업명"],
        y=sub["순이익"],
        text=sub["라벨"],
        textposition="outside",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>순이익: %{text}<extra></extra>",
    ))
    n_pos = (sub["순이익"] >= 0).sum()
    n_neg = (sub["순이익"] < 0).sum()
    apply(fig, {
        "title": f"기업별 순이익  |  흑자 {n_pos}개 · 적자 {n_neg}개",
        "xaxis": dict(title="", tickangle=-35, showgrid=False),
        "yaxis": dict(title="순이익 (원)", showgrid=True, gridcolor="#f1f5f9", zeroline=True, zerolinecolor="#94a3b8"),
        "shapes": [dict(
            type="line", x0=-0.5, x1=len(sub)-0.5, y0=0, y1=0,
            line=dict(color="#94a3b8", width=1, dash="dot"),
        )],
    })
    return fig


def employee_bar(df: pd.DataFrame):
    sub = df[["기업명", "고용인원(명)"]].dropna().sort_values("고용인원(명)", ascending=False)
    if sub.empty:
        return None
    total_emp = int(sub["고용인원(명)"].sum())
    sub["비율(%)"] = (sub["고용인원(명)"] / total_emp * 100).round(1)
    sub["라벨"] = sub.apply(lambda r: f"{int(r['고용인원(명)'])}명 ({r['비율(%)']:.1f}%)", axis=1)

    fig = go.Figure(go.Bar(
        x=sub["기업명"],
        y=sub["고용인원(명)"],
        text=sub["라벨"],
        textposition="outside",
        marker=dict(
            color=sub["고용인원(명)"],
            colorscale=[[0, "#fff7ed"], [1, "#ea580c"]],
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    apply(fig, {
        "title": f"기업별 고용 인원  (총 {total_emp:,}명)",
        "xaxis": dict(title="", tickangle=-35, showgrid=False),
        "yaxis": dict(title="고용 인원 (명)", showgrid=True, gridcolor="#f1f5f9"),
    })
    return fig


def invest_vs_revenue_scatter(df: pd.DataFrame):
    sub = df[["기업명", "총 투자 유치 금액", "매출", "최근 투자 단계", "대분야"]].dropna(
        subset=["총 투자 유치 금액", "매출"]
    )
    if sub.empty:
        return None
    sub["투자라벨"] = sub["총 투자 유치 금액"].apply(fmt_krw)
    sub["매출라벨"] = sub["매출"].apply(fmt_krw)

    fig = px.scatter(
        sub,
        x="총 투자 유치 금액", y="매출",
        color="최근 투자 단계",
        hover_name="기업명",
        size="매출", size_max=40,
        color_discrete_sequence=CAT_COLORS,
        log_x=True, log_y=True,
        labels={"총 투자 유치 금액": "총 투자 유치 금액 (원, 로그)", "매출": "매출 (원, 로그)"},
        custom_data=["투자라벨", "매출라벨", "대분야"],
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>투자: %{customdata[0]}<br>매출: %{customdata[1]}<br>분야: %{customdata[2]}<extra></extra>"
    )
    apply(fig, {"title": "총 투자 유치 금액 vs 매출 (로그 스케일)"})
    return fig


def rounds_vs_amount_scatter(df: pd.DataFrame):
    sub = df[["기업명", "총 투자 유치 횟수", "총 투자 유치 금액", "대분야", "최근 투자 단계"]].dropna(
        subset=["총 투자 유치 횟수", "총 투자 유치 금액"]
    )
    if sub.empty:
        return None
    sub["금액라벨"] = sub["총 투자 유치 금액"].apply(fmt_krw)
    fig = px.scatter(
        sub,
        x="총 투자 유치 횟수", y="총 투자 유치 금액",
        color="대분야",
        hover_name="기업명",
        size="총 투자 유치 금액", size_max=40,
        color_discrete_sequence=CAT_COLORS,
        labels={"총 투자 유치 횟수": "투자 유치 횟수 (회)", "총 투자 유치 금액": "총 투자 금액 (원)"},
        custom_data=["금액라벨", "최근 투자 단계"],
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>유치 횟수: %{x}회<br>총 금액: %{customdata[0]}<br>단계: %{customdata[1]}<extra></extra>"
    )
    apply(fig, {"title": "투자 유치 횟수 vs 총 투자 금액"})
    return fig
