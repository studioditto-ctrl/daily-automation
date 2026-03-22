"""
RS(상대강도) 계산기 - FinanceDataReader 기반

- pykrx 의 전종목/특정일 API 대신 FinanceDataReader 로 개별 종목 조회
- ThreadPoolExecutor 로 병렬 조회 (약 2-3분 소요)
- FinanceDataReader 컬럼: Open, High, Low, Close, Volume (영문, 안정적)

RS 계산 공식 (IBD 방식):
  weighted = (3개월 수익률 x 40%) + (6개월 수익률 x 20%)
           + (9개월 수익률 x 20%) + (12개월 수익률 x 20%)
  RS 점수  = 전체 종목 중 상위 백분위 (0~99)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import FinanceDataReader as fdr
import config


# ── 기간별 가중치 (영업일 기준) ──
PERIODS = [
    (63,  0.40),   # 3개월
    (126, 0.20),   # 6개월
    (189, 0.20),   # 9개월
    (252, 0.20),   # 12개월
]

# 병렬 워커 수 (네트워크 I/O 바운드 작업)
MAX_WORKERS = 16


def _today() -> str:
    return datetime.today().strftime("%Y%m%d")


def _get_stock_list() -> list[dict]:
    """전체 종목 목록 조회 (KOSPI + KOSDAQ via FinanceDataReader)"""
    stocks = []
    for market in config.RS_MARKETS:
        try:
            df = fdr.StockListing(market)
            for _, row in df.iterrows():
                stocks.append({
                    "code":   str(row["Code"]).zfill(6),
                    "name":   str(row.get("Name", "")),
                    "market": market,
                    "sector": str(row.get("Dept", "")),
                })
        except Exception as e:
            print(f"[RS Calc] {market} 목록 오류: {e}")
    return stocks


def _fetch_ohlcv(code: str, start: str, end: str) -> pd.DataFrame | None:
    """
    개별 종목 OHLCV 조회 (FinanceDataReader)

    Returns DataFrame with columns: Open, High, Low, Close, Volume
    """
    try:
        df = fdr.DataReader(code, start, end)
        if df is None or df.empty or "Close" not in df.columns:
            return None
        return df
    except Exception:
        return None


def _close_at_offset(df: pd.DataFrame, offset: int) -> float | None:
    """
    offset 영업일 전 종가 반환

    offset=0: 가장 최근 종가
    offset=63: 63 영업일 전 종가
    """
    min_rows = offset + 1
    if len(df) < min_rows:
        return None
    idx = -(offset + 1) if offset > 0 else -1
    val = df["Close"].iloc[idx]
    return float(val) if pd.notna(val) and float(val) > 0 else None


def _calc_weighted_return(df: pd.DataFrame) -> float | None:
    """4기간 가중 수익률 계산"""
    price_now = _close_at_offset(df, 0)
    if price_now is None:
        return None

    weighted = 0.0
    for days, weight in PERIODS:
        past = _close_at_offset(df, days)
        if past is None or past == 0:
            return None   # 4기간 모두 유효해야 함
        ret = (price_now / past - 1) * 100
        weighted += ret * weight

    return weighted


def calculate_rs() -> list[dict]:
    """
    전체 종목 RS 계산 및 점수 반환

    Returns:
        [{code, name, rs_score, sector, market}] RS 점수 내림차순
    """
    print("[RS Calc] 종목 목록 조회 중...")
    stocks = _get_stock_list()
    if not stocks:
        print("[RS Calc] 종목 목록 없음")
        return []

    print(f"[RS Calc] 총 {len(stocks)}개 종목 OHLCV 병렬 조회 시작 (워커={MAX_WORKERS})...")

    today = datetime.today()
    end_date   = today.strftime("%Y-%m-%d")
    # 252 영업일(1년) + 여유 (약 400 달력일)
    start_date = (today - timedelta(days=400)).strftime("%Y-%m-%d")

    # 각 종목별 가중 수익률 계산
    weighted_returns: dict[str, float] = {}
    done = 0

    def _process(stock: dict) -> tuple[str, float] | None:
        df = _fetch_ohlcv(stock["code"], start_date, end_date)
        if df is None:
            return None
        wr = _calc_weighted_return(df)
        if wr is None:
            return None
        return stock["code"], wr

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_process, s): s for s in stocks}
        for fut in as_completed(futures):
            done += 1
            if done % 300 == 0:
                print(f"[RS Calc] {done}/{len(stocks)} 처리 중...")
            res = fut.result()
            if res:
                code, wr = res
                weighted_returns[code] = wr

    if not weighted_returns:
        print("[RS Calc] 유효한 데이터 없음")
        return []

    print(f"[RS Calc] 유효 종목: {len(weighted_returns)}개, RS 점수 계산 중...")

    # 백분위 계산 -> 0~99점
    series = pd.Series(weighted_returns)
    ranks  = series.rank(pct=True) * 99
    ranks  = ranks.round(1)

    # 종목 정보 매핑
    info_by_code = {s["code"]: s for s in stocks}

    results = []
    for code, rs_score in ranks.items():
        info = info_by_code.get(code, {})
        results.append({
            "code":     code,
            "name":     info.get("name", ""),
            "rs_score": float(rs_score),
            "sector":   info.get("sector", ""),
            "market":   info.get("market", ""),
        })

    results.sort(key=lambda x: x["rs_score"], reverse=True)
    print(f"[RS Calc] RS 계산 완료: {len(results)}개 종목")
    return results


def run_collection() -> list[dict]:
    """
    RS 상위 후보군 반환 (config.RS_THRESHOLD 이상, config.MAX_FIRST_CANDIDATES개)
    """
    all_stocks = calculate_rs()
    if not all_stocks:
        return []

    filtered = [s for s in all_stocks if s["rs_score"] >= config.RS_THRESHOLD]
    result   = filtered[:config.MAX_FIRST_CANDIDATES]
    print(f"[RS Calc] RS {config.RS_THRESHOLD}점 이상: {len(filtered)}개 -> 상위 {len(result)}개 반환")
    return result


if __name__ == "__main__":
    results = run_collection()
    print(f"\n수집 결과: {len(results)}개")
    for r in results[:10]:
        print(f"  {r['code']} {r['name']:<12} RS={r['rs_score']:.1f} ({r['market']})")
