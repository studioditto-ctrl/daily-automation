"""사이드바 필터 UI"""
import streamlit as st
import pandas as pd


def render_sidebar(df: pd.DataFrame) -> dict:
    filters = {}
    with st.sidebar:
        st.header("필터")

        all_fields = sorted(df["대분야"].dropna().unique().tolist())
        sel_fields = st.multiselect("대분야", all_fields, default=all_fields, key="f_field")
        if len(sel_fields) < len(all_fields):
            filters["major_fields"] = sel_fields

        all_stages = df["최근 투자 단계"].dropna().unique().tolist()
        sel_stages = st.multiselect("투자 단계", all_stages, default=all_stages, key="f_stage")
        if len(sel_stages) < len(all_stages):
            filters["stages"] = sel_stages

        all_tech = sorted(df["기술"].dropna().unique().tolist())
        sel_tech = st.multiselect("기술 분류", all_tech, default=all_tech, key="f_tech")
        if len(sel_tech) < len(all_tech):
            filters["tech_types"] = sel_tech

        st.divider()
        if st.button("필터 초기화", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("f_"):
                    del st.session_state[k]
            st.rerun()

    return filters
