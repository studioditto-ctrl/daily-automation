"""산업·기술·투자단계 차트"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from charts._theme import apply, CAT_COLORS, BLUE_SEQ, pct_label, fmt_krw


def _add_pct(df: pd.DataFrame, count_col: str = "기업수") -> pd.DataFrame:
    total = df[count_col].sum()
    df = df.copy()
    df["비율(%)"] = (df[count_col] / total * 100).round(1)
    df["라벨"] = df.apply(lambda r: f"{int(r[count_col])}개 ({r['비율(%)']:.1f}%)", axis=1)
    return df, total


def major_field_treemap(field_df: pd.DataFrame, metric: str = "기업수"):
    if field_df.empty:
        return None
    df, total = _add_pct(field_df) if metric == "기업수" else (field_df.copy(), None)
    if metric not in df.columns:
        metric = "기업수"
    custom = df.copy()
    if "비율(%)" in custom.columns:
        custom["표시"] = custom["라벨"]
    else:
        custom["표시"] = custom[metric].apply(lambda v: f"{fmt_krw(v)}")

    fig = px.treemap(
        custom,
        path=["대분야"],
        values=metric,
        custom_data=["표시"],
        title=f"대분야별 {metric}",
        color=metric,
        color_continuous_scale=BLUE_SEQ,
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[0]}",
        textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>" + metric + ": %{customdata[0]}<extra></extra>",
    )
    apply(fig, {"height": 400, "coloraxis_showscale": False})
    return fig


def major_field_bar(field_df: pd.DataFrame, metric: str = "기업수"):
    if field_df.empty:
        return None
    df, total = _add_pct(field_df) if metric == "기업수" else (field_df.copy(), None)
    data = df.sort_values(metric)

    if metric == "기업수" and "라벨" in data.columns:
        text_col = "라벨"
    else:
        text_col = None

    fig = go.Figure(go.Bar(
        y=data["대분야"],
        x=data[metric],
        orientation="h",
        text=data[text_col] if text_col else data[metric].apply(fmt_krw),
        textposition="outside",
        marker=dict(
            color=data[metric],
            colorscale=BLUE_SEQ,
            showscale=False,
            line=dict(width=0),
        ),
    ))
    apply(fig, {
        "title": f"대분야별 {metric}",
        "xaxis": dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        "yaxis": dict(showgrid=False),
        "height": 380,
    })
    return fig


def minor_field_bar(minor_df: pd.DataFrame):
    if minor_df.empty:
        return None
    df, total = _add_pct(minor_df)
    data = df.sort_values("기업수")
    fig = go.Figure(go.Bar(
        y=data["소분야"],
        x=data["기업수"],
        orientation="h",
        text=data["라벨"],
        textposition="outside",
        marker=dict(
            color=data["기업수"],
            colorscale=[[0, "#d1fae5"], [1, "#059669"]],
            showscale=False,
            line=dict(width=0),
        ),
    ))
    apply(fig, {
        "title": "소분야별 기업 수 및 구성비",
        "xaxis": dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        "yaxis": dict(showgrid=False),
        "height": max(350, len(minor_df) * 30),
    })
    return fig


def tech_pie(tech_df: pd.DataFrame):
    if tech_df.empty:
        return None
    total = tech_df["기업수"].sum()
    fig = go.Figure(go.Pie(
        labels=tech_df["기술"],
        values=tech_df["기업수"],
        texttemplate="<b>%{label}</b><br>%{value}개<br>(%{percent})",
        textposition="outside",
        hole=0.45,
        marker=dict(colors=CAT_COLORS, line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>%{value}개 (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>총 {total}개</b><br>기업", x=0.5, y=0.5,
        font_size=13, showarrow=False, align="center",
    )
    apply(fig, {"title": "기술 분류별 구성비", "showlegend": True, "height": 400})
    return fig


def tech_bar(tech_df: pd.DataFrame):
    if tech_df.empty:
        return None
    df, _ = _add_pct(tech_df)
    data = df.sort_values("기업수")
    fig = go.Figure(go.Bar(
        y=data["기술"],
        x=data["기업수"],
        orientation="h",
        text=data["라벨"],
        textposition="outside",
        marker=dict(
            color=data["기업수"],
            colorscale=[[0, "#ede9fe"], [1, "#7c3aed"]],
            showscale=False,
            line=dict(width=0),
        ),
    ))
    apply(fig, {
        "title": "기술 분류별 기업 수 및 구성비",
        "xaxis": dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        "yaxis": dict(showgrid=False),
    })
    return fig


def stage_bar(stage_df: pd.DataFrame, metric: str = "기업수"):
    if stage_df.empty:
        return None
    df = stage_df.copy()
    if metric not in df.columns:
        metric = "기업수"

    if metric == "기업수":
        total = df[metric].sum()
        df["라벨"] = df[metric].apply(lambda v: f"{int(v)}개 ({v/total*100:.1f}%)")
        text = df["라벨"]
    else:
        text = df[metric].apply(fmt_krw)

    colors = CAT_COLORS[:len(df)]
    fig = go.Figure(go.Bar(
        x=df["최근 투자 단계"],
        y=df[metric],
        text=text,
        textposition="outside",
        marker=dict(color=colors, line=dict(color="white", width=1)),
    ))
    apply(fig, {
        "title": f"투자 단계별 {metric}",
        "xaxis": dict(title="투자 단계", showgrid=False),
        "yaxis": dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        "showlegend": False,
    })
    return fig


def stage_pie(stage_df: pd.DataFrame):
    if stage_df.empty:
        return None
    total = stage_df["기업수"].sum()
    fig = go.Figure(go.Pie(
        labels=stage_df["최근 투자 단계"],
        values=stage_df["기업수"],
        texttemplate="<b>%{label}</b><br>%{value}개 (%{percent})",
        textposition="outside",
        hole=0.45,
        marker=dict(colors=CAT_COLORS, line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>%{value}개 (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>총 {total}개</b><br>기업", x=0.5, y=0.5,
        font_size=13, showarrow=False, align="center",
    )
    apply(fig, {"title": "투자 단계별 구성비", "showlegend": True, "height": 400})
    return fig


def stage_field_heatmap(cross_df: pd.DataFrame):
    if cross_df.empty:
        return None
    # 행(대분야) 합계로 % 계산
    row_totals = cross_df.sum(axis=1)
    pct_df = cross_df.div(row_totals, axis=0) * 100

    text_vals = []
    for i, row in cross_df.iterrows():
        row_txt = []
        for j, col in enumerate(cross_df.columns):
            v = int(row[col])
            p = pct_df.loc[i, col]
            row_txt.append(f"{v}개<br>{p:.0f}%" if v > 0 else "")
        text_vals.append(row_txt)

    fig = go.Figure(go.Heatmap(
        z=cross_df.values,
        x=cross_df.columns.tolist(),
        y=cross_df.index.tolist(),
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale=[[0, "#f8fafc"], [0.5, "#93c5fd"], [1, "#1e3a5f"]],
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>%{text}<extra></extra>",
        showscale=True,
        colorbar=dict(thickness=12, len=0.8, title="기업수"),
    ))
    apply(fig, {
        "title": "대분야 × 투자 단계 매트릭스 (기업수 / 행 비율)",
        "xaxis": dict(title="투자 단계", side="bottom"),
        "yaxis": dict(title="대분야"),
        "height": 420,
    })
    return fig
