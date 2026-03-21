"""
THE VC 엑셀 파일 로드 및 정제 모듈
"""
import io
import pandas as pd
import numpy as np

from config import COLUMN_MAP, NA_STRINGS


def load_excel(uploaded_file) -> pd.DataFrame:
    """Streamlit UploadedFile 또는 파일 경로에서 DataFrame 로드."""
    if isinstance(uploaded_file, (str, bytes.__class__)):
        # 파일 경로인 경우
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    else:
        file_bytes = uploaded_file.read()
        fname = getattr(uploaded_file, "name", "").lower()
        engine = "xlrd" if fname.endswith(".xls") else "openpyxl"
        df = pd.read_excel(io.BytesIO(file_bytes), engine=engine)

    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    THE VC 형식 데이터 정제:
    - NA 문자열 → NaN
    - 수치 컬럼 파싱
    - 날짜 파싱
    """
    df = df.copy()

    # NA 문자열 처리
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if str(x).strip() in NA_STRINGS else x)

    # 수치 컬럼
    for col in ["매출", "순이익", "총 투자 유치 금액", "고용인원(명)", "총 투자 유치 횟수"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 날짜 컬럼
    if "최근 투자 유치일" in df.columns:
        df["최근 투자 유치일"] = pd.to_datetime(df["최근 투자 유치일"], errors="coerce")
        df["투자연도"] = df["최근 투자 유치일"].dt.year.astype("Int64")

    # 스테이지 정리
    if "최근 투자 단계" in df.columns:
        df["최근 투자 단계"] = df["최근 투자 단계"].fillna("해당 없음")

    return df


def parse_investors(investors_series: pd.Series) -> list[str]:
    """
    '주요 투자자' 컬럼의 쉼표 구분 투자자 목록을 flat list로 반환.
    괄호 안 횟수 표기 제거 (예: '팁스(2회)' → '팁스')
    """
    import re
    investors = []
    for val in investors_series.dropna():
        for name in str(val).split(","):
            name = name.strip()
            name = re.sub(r"\(\d+회\)", "", name).strip()
            if name and name not in NA_STRINGS:
                investors.append(name)
    return investors


def get_investor_counts(investors_series: pd.Series) -> pd.DataFrame:
    """투자자별 참여 기업 수 집계."""
    names = parse_investors(investors_series)
    counts = pd.Series(names).value_counts().reset_index()
    counts.columns = ["투자자", "참여 기업 수"]
    return counts
