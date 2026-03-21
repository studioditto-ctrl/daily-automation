"""
Agent 2: Chart Analyst — 차트 분석 및 2차 후보군 선정

Claude API tool_use 패턴으로 동작:
  1. fetch_chart_data          : pykrx로 종목별 OHLCV 수집
  2. check_breakout_conditions : 돌파 조건 검사
  3. save_second_stage         : 2차 후보군 저장
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import anthropic
import config
from analyzers.pykrx_client import get_ohlcv, get_stock_name
from analyzers.breakout_strategy import check_breakout, suggest_entry_price
from storage.data_store import save_candidates, today_str


# ──────────────────────────────────────────
# 도구 정의
# ──────────────────────────────────────────
TOOLS = [
    {
        "name": "fetch_chart_data",
        "description": (
            "pykrx를 사용해 종목의 일봉 OHLCV 데이터를 가져옵니다. "
            "반환값: {code, name, ohlcv_summary, latest_close, volume_ratio}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "종목코드 6자리 (예: '005930')",
                },
                "period": {
                    "type": "integer",
                    "description": f"조회 영업일 수 (기본: {config.LOOKBACK_DAYS})",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "check_breakout_conditions",
        "description": (
            "종목의 OHLCV 데이터를 기반으로 돌파매매 조건을 검사합니다. "
            "52주 신고가 돌파, 박스권 돌파, 거래량 급등, 이평선 정배열 여부를 반환합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "종목코드",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "save_second_stage",
        "description": "2차 후보군을 오늘 날짜로 저장합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "description": "돌파 조건을 충족한 최종 후보군 리스트",
                    "items": {"type": "object"},
                },
            },
            "required": ["candidates"],
        },
    },
]


# ──────────────────────────────────────────
# 인메모리 OHLCV 캐시 (Agent 루프 내 중복 조회 방지)
# ──────────────────────────────────────────
_ohlcv_cache: dict = {}


def _get_ohlcv_cached(code: str, period: int):
    if code not in _ohlcv_cache:
        _ohlcv_cache[code] = get_ohlcv(code, period)
    return _ohlcv_cache[code]


# ──────────────────────────────────────────
# 도구 실행 함수
# ──────────────────────────────────────────
def _execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "fetch_chart_data":
        code = tool_input["code"]
        period = tool_input.get("period", config.LOOKBACK_DAYS)
        df = _get_ohlcv_cached(code, period)
        name = get_stock_name(code)

        if df.empty:
            return json.dumps({"error": f"{code} 데이터 없음"})

        latest = df.iloc[-1]
        avg_vol = df["Volume"].iloc[-21:-1].mean() if len(df) >= 21 else 1
        vol_ratio = round(float(latest["Volume"]) / avg_vol, 2) if avg_vol > 0 else 0

        return json.dumps({
            "code": code,
            "name": name,
            "data_points": len(df),
            "latest_close": float(latest["Close"]),
            "latest_high": float(latest["High"]),
            "latest_volume": int(latest["Volume"]),
            "volume_ratio": vol_ratio,
            "52w_high": float(df["High"].max()),
            "period_low": float(df["Low"].min()),
        }, ensure_ascii=False)

    elif tool_name == "check_breakout_conditions":
        code = tool_input["code"]
        df = _get_ohlcv_cached(code, config.LOOKBACK_DAYS)

        if df.empty:
            return json.dumps({"code": code, "passed": False, "signals": [], "score": 0})

        result = check_breakout(df)
        entry_info = suggest_entry_price(df)

        return json.dumps({
            "code": code,
            "passed": result["passed"],
            "signals": result["signals"],
            "score": result["score"],
            "min_score": result["min_score"],
            "entry_price": entry_info.get("entry"),
            "stop_price": entry_info.get("stop"),
            "target_price": entry_info.get("target"),
        }, ensure_ascii=False)

    elif tool_name == "save_second_stage":
        candidates = tool_input.get("candidates", [])
        date_str = today_str()
        path = save_candidates(date_str, stage=2, candidates=candidates)
        return json.dumps({"saved_path": path, "count": len(candidates), "date": date_str})

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ──────────────────────────────────────────
# Agent 메인 루프
# ──────────────────────────────────────────
class ChartAnalystAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL

    def run(self, first_stage: list[dict]) -> list[dict]:
        """
        2차 후보군 선정 실행

        Args:
            first_stage: DataCollectorAgent가 반환한 1차 후보군

        Returns:
            2차 후보군 종목 리스트. 실패 시 빈 리스트.
        """
        if not first_stage:
            print("[ChartAnalyst] 1차 후보군이 비어 있음, 종료")
            return []

        print(f"[ChartAnalyst] Agent 시작 — 1차 후보군 {len(first_stage)}개 분석")
        _ohlcv_cache.clear()

        system_prompt = (
            "당신은 한국 주식 기술적 분석 전문가입니다. "
            "1차 후보군 종목들을 대상으로 돌파매매 조건을 검사하여 2차 후보군을 선정하세요.\n\n"
            "실행 순서:\n"
            "1. 각 종목에 대해 fetch_chart_data로 차트 데이터 조회\n"
            "2. check_breakout_conditions로 돌파 조건 검사\n"
            "3. 조건 충족 종목만 모아 save_second_stage로 저장\n"
            "4. 최종 선정 결과 요약 리포트 출력 (종목명, 충족 조건, 진입가 포함)"
        )

        codes_str = ", ".join([f"{s['code']}({s.get('name', '')})" for s in first_stage])
        user_message = (
            f"다음 1차 후보군 {len(first_stage)}개 종목을 분석하여 "
            f"돌파매매 2차 후보군을 선정하세요.\n\n"
            f"종목 목록: {codes_str}\n\n"
            f"조건 충족 기준: 돌파 점수 2점 이상 (4가지 조건 중 2개 이상 충족)\n"
            f"최대 {config.MAX_SECOND_CANDIDATES}개까지 선정"
        )

        messages = [{"role": "user", "content": user_message}]
        second_stage_candidates: list[dict] = []

        # Agentic loop
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                print("[ChartAnalyst] Agent 완료")
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"[ChartAnalyst] {block.text}")
                break

            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    print(f"[ChartAnalyst] 도구 실행: {block.name} {block.input.get('code', '')}")
                    result_str = _execute_tool(block.name, block.input)
                    result_data = json.loads(result_str)

                    # 2차 후보군 캡처
                    if block.name == "save_second_stage":
                        second_stage_candidates = tool_input_candidates = block.input.get("candidates", [])

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

                messages.append({"role": "user", "content": tool_results})
            else:
                break

        print(f"[ChartAnalyst] 2차 후보군: {len(second_stage_candidates)}개")
        return second_stage_candidates


# 직접 실행 시 테스트
if __name__ == "__main__":
    mock_first_stage = [
        {"code": "005930", "name": "삼성전자", "rs_score": 92},
        {"code": "000660", "name": "SK하이닉스", "rs_score": 88},
        {"code": "035720", "name": "카카오", "rs_score": 81},
    ]
    agent = ChartAnalystAgent()
    result = agent.run(mock_first_stage)
    print(f"\n2차 후보군 {len(result)}개:")
    for r in result:
        print(r)
