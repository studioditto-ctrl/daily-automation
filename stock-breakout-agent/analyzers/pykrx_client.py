"""
FinanceDataReader 기반 한국 주식 OHLCV 데이터 래퍼
- 일봉 데이터, 52주 신고가, 거래량 배수 등 제공
- FinanceDataReader: 영문 컬럼 (Open, High, Low, Close, Volume)
"""
from datetime import datetime, timedelta

import pandas as pd
import FinanceDataReader as fdr

import config


def _to_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def get_ohlcv(code: str, period: int = None) -> pd.DataFrame:
    """
    종목 일봉 OHLCV 반환

    Args:
        code: 종목코드 (예: '005930')
        period: 조회 영업일 수 (기본값: config.LOOKBACK_DAYS)

    Returns:
        DataFrame (columns: Open, High, Low, Close, Volume, index: date)
        빈 DataFrame 반환 시 데이터 없음
    """
    if period is None:
        period = config.LOOKBACK_DAYS

    end = datetime.today()
    # 영업일 기준 period일 약 달력 기준 period * 1.5일 (주말/공휴일 여유분)
    start = end - timedelta(days=int(period * 1.5))

    try:
        df = fdr.DataReader(code, _to_str(start), _to_str(end))
    except Exception:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    df.index = pd.to_datetime(df.index)

    # FinanceDataReader 컬럼: Open, High, Low, Close, Volume
    required = ["Open", "High", "Low", "Close", "Volume"]
    available = [c for c in required if c in df.columns]
    if len(available) < 4:
        return pd.DataFrame()

    df = df[available].copy()
    return df.tail(period)


def get_52w_high(code: str) -> float:
    """52주(약 250 영업일) 최고가 반환. 데이터 없으면 0.0"""
    df = get_ohlcv(code, period=250)
    if df.empty or "High" not in df.columns:
        return 0.0
    return float(df["High"].max())


def get_volume_ratio(code: str, period: int = 20) -> float:
    """
    당일 거래량 / 최근 N일 평균 거래량 비율 반환.
    데이터 부족 시 0.0 반환.
    """
    df = get_ohlcv(code, period=period + 1)
    if df.empty or "Volume" not in df.columns or len(df) < 2:
        return 0.0
    avg_volume = df["Volume"].iloc[:-1].mean()
    today_volume = df["Volume"].iloc[-1]
    if avg_volume == 0:
        return 0.0
    return round(float(today_volume / avg_volume), 2)


def get_moving_averages(df: pd.DataFrame, windows: list[int] = None) -> dict[int, pd.Series]:
    """
    이동평균선 계산

    Args:
        df: get_ohlcv() 반환 DataFrame
        windows: 이평선 기간 리스트 (기본: [5, 20, 60, 120])

    Returns:
        {기간: Series} 딕셔너리
    """
    if windows is None:
        windows = [5, 20, 60, 120]
    if "Close" not in df.columns:
        return {}
    return {w: df["Close"].rolling(w).mean() for w in windows}


def get_stock_name(code: str) -> str:
    """종목코드 -> 종목명 반환. 실패 시 빈 문자열"""
    try:
        listing = fdr.StockListing("KRX")
        row = listing[listing["Code"] == code]
        if not row.empty:
            return str(row.iloc[0].get("Name", ""))
    except Exception:
        pass
    return ""
