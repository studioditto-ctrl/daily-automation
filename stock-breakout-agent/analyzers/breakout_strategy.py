"""
돌파매매 전략 조건 검사 모듈

[ 사용자 설정 가이드 ]
이 파일의 check_breakout() 함수에 실제 돌파 조건을 구현하세요.
현재 기본 조건 4가지가 예시로 구현되어 있으며, 자유롭게 수정·추가할 수 있습니다.

기본 제공 조건:
  1. 52주 신고가 돌파  (W52_BREAKOUT)
  2. 박스권 상단 돌파  (BOX_BREAKOUT)
  3. 거래량 급등 동반  (VOLUME_SURGE)
  4. 이동평균선 정배열 (MA_ALIGNMENT)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import config


# ──────────────────────────────────────────
# 조건별 임계값 (환경변수 또는 여기서 직접 수정)
# ──────────────────────────────────────────
BOX_PERIOD = int(os.getenv("BOX_PERIOD", "60"))          # 박스권 기준 기간 (영업일)
VOLUME_SURGE_RATIO = float(os.getenv("VOLUME_SURGE_RATIO", "1.5"))  # 거래량 급등 배수
W52_BUFFER_PCT = float(os.getenv("W52_BUFFER_PCT", "0.98"))         # 신고가의 몇 % 이상이면 돌파로 판단


def _check_52w_breakout(df: pd.DataFrame) -> tuple[bool, str]:
    """
    52주 신고가 돌파 여부
    - 오늘 종가 >= 52주 고가의 W52_BUFFER_PCT
    """
    if len(df) < 2:
        return False, ""
    high_52w = df["High"].max()
    today_close = df["Close"].iloc[-1]
    passed = today_close >= high_52w * W52_BUFFER_PCT
    signal = f"52주 신고가 돌파 (현재:{today_close:,.0f} / 신고가:{high_52w:,.0f})" if passed else ""
    return passed, signal


def _check_box_breakout(df: pd.DataFrame) -> tuple[bool, str]:
    """
    박스권 상단 돌파 여부
    - 오늘 종가 > 최근 BOX_PERIOD일 고점 (단, 오늘 제외)
    """
    if len(df) < BOX_PERIOD + 1:
        return False, ""
    box_high = df["High"].iloc[-(BOX_PERIOD + 1):-1].max()
    today_close = df["Close"].iloc[-1]
    passed = today_close > box_high
    signal = f"박스권 상단 돌파 ({BOX_PERIOD}일 고점:{box_high:,.0f})" if passed else ""
    return passed, signal


def _check_volume_surge(df: pd.DataFrame) -> tuple[bool, str]:
    """
    거래량 급등 동반 여부
    - 오늘 거래량 >= 최근 20일 평균 거래량 * VOLUME_SURGE_RATIO
    """
    if len(df) < 21:
        return False, ""
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    today_vol = df["Volume"].iloc[-1]
    ratio = today_vol / avg_vol if avg_vol > 0 else 0
    passed = ratio >= VOLUME_SURGE_RATIO
    signal = f"거래량 급등 ({ratio:.1f}배)" if passed else ""
    return passed, signal


def _check_ma_alignment(df: pd.DataFrame) -> tuple[bool, str]:
    """
    이동평균선 정배열 여부
    - 종가 > 5일 > 20일 > 60일 순서로 정배열
    """
    if len(df) < 60:
        return False, ""
    close = df["Close"].iloc[-1]
    ma5  = df["Close"].rolling(5).mean().iloc[-1]
    ma20 = df["Close"].rolling(20).mean().iloc[-1]
    ma60 = df["Close"].rolling(60).mean().iloc[-1]
    passed = close > ma5 > ma20 > ma60
    signal = "이평선 정배열 (종가>5>20>60)" if passed else ""
    return passed, signal


# ──────────────────────────────────────────
# 메인 진입점 — 이 함수를 수정하여 조건 커스터마이징
# ──────────────────────────────────────────
def check_breakout(df: pd.DataFrame, cfg: dict | None = None) -> dict:
    """
    돌파 조건 종합 검사

    Args:
        df:  pykrx_client.get_ohlcv() 반환 DataFrame
        cfg: 추가 설정 딕셔너리 (현재 미사용, 향후 확장용)

    Returns:
        {
            "passed": bool,         # 최소 조건 이상 충족 여부
            "signals": list[str],   # 충족된 조건 설명 목록
            "score": int,           # 충족된 조건 수
            "min_score": int,       # 통과 기준 최소 점수
        }
    """
    if df is None or df.empty:
        return {"passed": False, "signals": [], "score": 0, "min_score": 2}

    checks = [
        _check_52w_breakout(df),
        _check_box_breakout(df),
        _check_volume_surge(df),
        _check_ma_alignment(df),
    ]

    signals = [sig for passed, sig in checks if passed and sig]
    score = len(signals)

    # ──────────────────────────────────────
    # 통과 기준: 4개 조건 중 2개 이상 충족
    # ← 여기를 수정하여 기준을 강화/완화 가능
    # ──────────────────────────────────────
    min_score = 2
    passed = score >= min_score

    return {
        "passed": passed,
        "signals": signals,
        "score": score,
        "min_score": min_score,
    }


def suggest_entry_price(df: pd.DataFrame) -> dict:
    """
    진입가/손절가/목표가 제안 (단순 기술적 기준)

    Returns:
        {
            "entry": float,    # 전일 고가 + 1틱 (돌파 진입가)
            "stop":  float,    # 전일 저가 (손절가)
            "target": float,   # 진입가 대비 +10% (1차 목표가)
        }
    """
    if df is None or df.empty or len(df) < 2:
        return {}
    prev_high = float(df["High"].iloc[-2])
    prev_low  = float(df["Low"].iloc[-2])
    entry  = round(prev_high * 1.001, 0)   # 전일 고가 + 약 0.1%
    stop   = round(prev_low, 0)
    target = round(entry * 1.10, 0)         # 진입가 대비 +10%
    return {"entry": entry, "stop": stop, "target": target}
