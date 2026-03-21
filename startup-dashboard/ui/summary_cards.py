"""전문 금융 분석 KPI 카드"""
import streamlit as st


def _fmt_krw(val) -> str:
    if val is None:
        return "—"
    if val >= 1e12:
        return f"{val/1e12:.1f}조원"
    if val >= 1e8:
        return f"{val/1e8:.0f}억원"
    if val >= 1e4:
        return f"{val/1e4:.0f}만원"
    return f"{val:,.0f}원"


def render_kpi_cards(kpi: dict, total_df_len: int = None):
    """전문 금융 스타일 KPI 카드 4열 렌더링."""

    total    = kpi.get("total_companies", 0)
    t_invest = kpi.get("total_invest")
    m_invest = kpi.get("median_invest")
    t_emp    = kpi.get("total_employees")

    cards = [
        {
            "label": "분석 대상 기업",
            "value": f"{total}개사",
            "sub": f"전체 {total_df_len}개사 중" if total_df_len and total_df_len != total else "THE VC 8기 코호트",
            "color": "#1d4ed8",
            "icon": "🏢",
        },
        {
            "label": "총 투자 유치 금액",
            "value": _fmt_krw(t_invest) if t_invest else "—",
            "sub": f"기업당 평균 {_fmt_krw(t_invest/total) if t_invest and total else '—'}",
            "color": "#059669",
            "icon": "💰",
        },
        {
            "label": "중앙값 투자 금액",
            "value": _fmt_krw(m_invest) if m_invest else "—",
            "sub": "투자 분포 대표값 (중앙값)",
            "color": "#d97706",
            "icon": "📊",
        },
        {
            "label": "총 고용 인원",
            "value": f"{t_emp:,}명" if t_emp else "—",
            "sub": f"기업당 평균 {t_emp//total}명" if t_emp and total else "",
            "color": "#7c3aed",
            "icon": "👥",
        },
    ]

    cols = st.columns(4)
    for col, card in zip(cols, cards):
        with col:
            st.markdown(f"""
<div style="
    background: white;
    border: 1px solid #e2e8f0;
    border-top: 4px solid {card['color']};
    border-radius: 10px;
    padding: 20px 22px 16px;
    box-shadow: 0 1px 4px rgba(15,23,42,0.07);
    height: 130px;
">
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
        <span style="font-size:18px;">{card['icon']}</span>
        <span style="font-size:11px; font-weight:600; color:#64748b;
                     text-transform:uppercase; letter-spacing:0.6px;">
            {card['label']}
        </span>
    </div>
    <div style="font-size:26px; font-weight:700; color:#0f172a; line-height:1.1; margin-bottom:6px;">
        {card['value']}
    </div>
    <div style="font-size:11px; color:#94a3b8;">
        {card['sub']}
    </div>
</div>
""", unsafe_allow_html=True)
