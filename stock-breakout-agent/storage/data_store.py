"""
후보군 데이터 저장/조회 모듈
- 1차(RS 기반), 2차(돌파 조건) 후보군을 날짜별 JSON으로 관리
"""
import json
import os
from datetime import date, datetime
from typing import Optional

import config


def _report_path(target_date: str, stage: int) -> str:
    """날짜 + 단계별 파일 경로 반환 (stage: 1 또는 2)"""
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    return os.path.join(config.REPORTS_DIR, f"{target_date}_stage{stage}.json")


def save_candidates(target_date: str, stage: int, candidates: list[dict]) -> str:
    """
    후보군 저장

    Args:
        target_date: 'YYYY-MM-DD' 형식
        stage: 1 (RS 기반) or 2 (돌파 조건)
        candidates: 종목 리스트

    Returns:
        저장된 파일 경로
    """
    path = _report_path(target_date, stage)
    payload = {
        "date": target_date,
        "stage": stage,
        "saved_at": datetime.now().isoformat(),
        "count": len(candidates),
        "candidates": candidates,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_candidates(target_date: str, stage: int) -> Optional[dict]:
    """
    후보군 로드. 없으면 None 반환.
    """
    path = _report_path(target_date, stage)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_dates() -> list[str]:
    """
    저장된 날짜 목록 반환 (내림차순)
    """
    if not os.path.exists(config.REPORTS_DIR):
        return []
    dates = set()
    for fname in os.listdir(config.REPORTS_DIR):
        if fname.endswith(".json"):
            # 파일명 형식: YYYY-MM-DD_stageN.json
            parts = fname.split("_stage")
            if len(parts) == 2:
                dates.add(parts[0])
    return sorted(dates, reverse=True)


def today_str() -> str:
    return date.today().strftime("%Y-%m-%d")
