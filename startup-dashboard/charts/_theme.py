"""
전문 금융 분석 차트 공통 테마
"""

TEMPLATE = "plotly_white"

# 색상 팔레트
PRIMARY     = "#1e3a5f"
BLUE_SEQ    = ["#dbeafe", "#93c5fd", "#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#1e3a5f"]
CAT_COLORS  = ["#1d4ed8", "#d97706", "#059669", "#dc2626", "#7c3aed",
               "#0891b2", "#be123c", "#65a30d", "#c2410c", "#334155"]
POS_COLOR   = "#059669"
NEG_COLOR   = "#dc2626"
GRAY_COLOR  = "#94a3b8"

BASE_LAYOUT = dict(
    template=TEMPLATE,
    font=dict(family="'Helvetica Neue', Arial, sans-serif", size=12, color="#334155"),
    title_font=dict(
        size=14, color="#0f172a",
        family="'Helvetica Neue', Arial, sans-serif",
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=55, b=40, l=10, r=20),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0"),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#e2e8f0",
        borderwidth=1,
        font=dict(size=11),
    ),
)


def apply(fig, extra: dict | None = None):
    """차트에 기본 레이아웃 적용."""
    layout = {**BASE_LAYOUT}
    if extra:
        layout.update(extra)
    fig.update_layout(**layout)
    return fig


def fmt_krw(val: float) -> str:
    """금액 → 한국식 표기."""
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"{val/1e12:.1f}조"
    if val >= 1e8:
        return f"{val/1e8:.0f}억"
    if val >= 1e4:
        return f"{val/1e4:.0f}만"
    return f"{val:,.0f}"


def pct_label(value: float, total: float) -> str:
    """'값 (N%)' 형식 라벨."""
    if total == 0:
        return str(int(value))
    pct = value / total * 100
    return f"{int(value)} ({pct:.1f}%)"
