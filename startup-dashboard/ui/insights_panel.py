"""AI 인사이트 패널 UI"""
import hashlib
import streamlit as st
import pandas as pd

from core.ai_insights import StartupInsightAnalyzer, build_context


def render_insights_panel(df, field_df, tech_df, stage_df, investor_df, stats_df, api_key):
    st.subheader("Claude AI 인사이트")
    st.caption("현재 필터가 적용된 데이터를 기반으로 심층 분석을 제공합니다.")

    if not api_key:
        st.warning("사이드바에서 Anthropic API 키를 입력하면 AI 인사이트를 사용할 수 있습니다.")
        return

    cache_key = hashlib.md5(f"{len(df)}_{list(df.columns)}".encode()).hexdigest()[:12]

    if st.button("AI 인사이트 생성", type="primary", use_container_width=True):
        with st.spinner("Claude가 분석 중..."):
            try:
                analyzer = StartupInsightAnalyzer(api_key)
                ctx = build_context(df, field_df, tech_df, stage_df, investor_df, stats_df)
                result = analyzer.generate_full_report(ctx)
                if "ai_insights" not in st.session_state:
                    st.session_state["ai_insights"] = {}
                st.session_state["ai_insights"][cache_key] = result
            except Exception as e:
                st.error(f"분석 실패: {e}")
                return

    cached = st.session_state.get("ai_insights", {}).get(cache_key)
    if cached:
        st.markdown(cached)
        st.download_button("리포트 다운로드 (.md)", cached, "startup_ai_report.md", "text/markdown")
    else:
        st.info("버튼을 클릭하면 AI 분석을 시작합니다.")
