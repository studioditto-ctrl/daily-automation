"""
Orchestrator — 전체 워크플로우 조율

실행 순서:
  1. DataCollectorAgent  → 1차 후보군 (RS 기반)
  2. ChartAnalystAgent   → 2차 후보군 (돌파 조건)
  3. 실행 결과 요약 출력
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Windows cp949 콘솔에서 이모지/한자 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime
from agents.data_collector import DataCollectorAgent
from agents.chart_analyst import ChartAnalystAgent
from storage.data_store import load_candidates, today_str


MAX_RETRIES = 1  # 각 Agent 실패 시 재시도 횟수


async def _run_data_collector_with_retry() -> list[dict]:
    """DataCollectorAgent 실행 (실패 시 MAX_RETRIES회 재시도)"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            agent = DataCollectorAgent()
            result = await agent.run()
            if result:
                return result
            print(f"[Orchestrator] DataCollector 결과 없음 (시도 {attempt + 1})")
        except Exception as e:
            print(f"[Orchestrator] DataCollector 오류 (시도 {attempt + 1}): {e}")

        if attempt < MAX_RETRIES:
            print("[Orchestrator] 재시도 중...")
            await asyncio.sleep(5)

    return []


def _run_chart_analyst_with_retry(first_stage: list[dict]) -> list[dict]:
    """ChartAnalystAgent 실행 (실패 시 MAX_RETRIES회 재시도)"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            agent = ChartAnalystAgent()
            result = agent.run(first_stage)
            if result is not None:
                return result
            print(f"[Orchestrator] ChartAnalyst 결과 없음 (시도 {attempt + 1})")
        except Exception as e:
            print(f"[Orchestrator] ChartAnalyst 오류 (시도 {attempt + 1}): {e}")

        if attempt < MAX_RETRIES:
            print("[Orchestrator] 재시도 중...")

    return []


def _print_summary(first_stage: list[dict], second_stage: list[dict], elapsed: float):
    """실행 결과 요약 출력"""
    date_str = today_str()
    print("\n" + "=" * 60)
    print(f"  돌파매매 후보군 선별 완료 [{date_str}]")
    print("=" * 60)
    print(f"  1차 후보군 (RS 기반):   {len(first_stage):>3}개")
    print(f"  2차 후보군 (돌파 조건): {len(second_stage):>3}개")
    print(f"  소요 시간: {elapsed:.1f}초")
    print("-" * 60)

    if second_stage:
        print("  [ 2차 후보군 ]")
        for i, s in enumerate(second_stage[:10], 1):
            code = s.get("code", "")
            name = s.get("name", "")
            rs   = s.get("rs_score", "-")
            sigs = s.get("signals", [])
            entry = s.get("entry_price", "-")
            print(f"  {i:>2}. {code} {name:<12} RS:{rs}  진입가:{entry}  조건:{len(sigs)}개")
        if len(second_stage) > 10:
            print(f"  ... 외 {len(second_stage) - 10}개")
    else:
        print("  오늘은 돌파 조건을 충족한 종목이 없습니다.")

    print("=" * 60)


async def run_daily() -> dict:
    """
    일일 파이프라인 실행 진입점

    Returns:
        {
            "date": str,
            "first_stage": list[dict],
            "second_stage": list[dict],
            "elapsed_seconds": float,
        }
    """
    start_time = datetime.now()
    print(f"\n[Orchestrator] 파이프라인 시작 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Step 1: 1차 후보군 수집 ──
    print("\n[Orchestrator] Step 1: RS 데이터 수집 중...")
    first_stage = await _run_data_collector_with_retry()

    if not first_stage:
        print("[Orchestrator] 1차 후보군 수집 실패. 저장된 데이터 확인 중...")
        # 오늘 저장된 데이터가 있으면 재활용
        saved = load_candidates(today_str(), stage=1)
        if saved:
            first_stage = saved.get("candidates", [])
            print(f"[Orchestrator] 저장된 1차 후보군 {len(first_stage)}개 로드")

    # ── Step 2: 2차 후보군 선정 ──
    print(f"\n[Orchestrator] Step 2: 차트 분석 중... ({len(first_stage)}개 종목)")
    second_stage = _run_chart_analyst_with_retry(first_stage) if first_stage else []

    elapsed = (datetime.now() - start_time).total_seconds()
    _print_summary(first_stage, second_stage, elapsed)

    return {
        "date": today_str(),
        "first_stage": first_stage,
        "second_stage": second_stage,
        "elapsed_seconds": elapsed,
    }


# 직접 실행
if __name__ == "__main__":
    asyncio.run(run_daily())
