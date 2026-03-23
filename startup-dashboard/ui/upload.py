"""
파일 업로드 UI
"""
import streamlit as st
import pandas as pd

from core.loader import load_excel, clean_dataframe


def render_upload_section() -> bool:
    """
    파일 업로드 UI. 분석 준비 완료 시 True 반환.
    """
    st.header("스타트업 DB 업로드")
    uploaded = st.file_uploader(
        "THE VC 엑셀 파일을 업로드하세요 (.xlsx / .xls)",
        type=["xlsx", "xls"],
    )

    if uploaded is None:
        st.info("THE VC에서 내려받은 스타트업 DB 파일을 업로드하면 자동으로 분석을 시작합니다.")
        # 로컬 경로 직접 로드 (개발/테스트용)
        with st.expander("로컬 파일 경로로 로드 (테스트용)"):
            local_path = st.text_input("파일 경로", key="local_path_input", placeholder="C:\\Users\\...")
            if st.button("경로로 로드", key="load_by_path") and local_path:
                import os
                if os.path.exists(local_path):
                    _reset_session()
                    try:
                        raw_df = load_excel(local_path)
                        clean_df = clean_dataframe(raw_df)
                        st.session_state["clean_df"] = clean_df
                        st.session_state["file_name"] = os.path.basename(local_path)
                        st.session_state["ready"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"로드 실패: {e}")
                else:
                    st.error("파일이 존재하지 않습니다.")
        return False

    # 새 파일이면 세션 초기화
    if st.session_state.get("file_name") != uploaded.name:
        _reset_session()
        st.session_state["file_name"] = uploaded.name

    if "clean_df" not in st.session_state:
        with st.spinner("파일을 불러오는 중..."):
            try:
                raw_df = load_excel(uploaded)
                clean_df = clean_dataframe(raw_df)
                st.session_state["clean_df"] = clean_df
                st.session_state["ready"] = True
            except Exception as e:
                st.error(f"파일 로드 실패: {e}")
                return False

    df = st.session_state["clean_df"]
    st.success(f"파일 로드 완료: **{len(df)}개 기업** / {len(df.columns)}개 컬럼")
    return st.session_state.get("ready", False)


def _reset_session():
    for key in ["clean_df", "ready", "ai_insights", "file_name"]:
        st.session_state.pop(key, None)
