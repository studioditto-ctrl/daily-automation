"""
Agent 1: Data Collector — RS 데이터 수집 및 1차 후보군 선정

Claude API tool_use 패턴으로 동작:
  1. fetch_rs_ranking  : Playwright로 사이트 RS 랭킹 수집
  2. filter_candidates : RS 점수 기준으로 1차 필터링
  3. save_first_stage  : 결과를 storage에 저장
"""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import anthropic
import config
from collectors.rs_crawler import run_collection
from storage.data_store import save_candidates, today_str


# ──────────────────────────────────────────
# 도구 정의 (Claude에게 노출할 함수 스펙)
# ──────────────────────────────────────────
TOOLS = [
    {
        "name": "fetch_rs_ranking",
        "description": (
            "StockEasy API를 호출하여 RS(상대강도) 랭킹 데이터를 수집합니다. "
            "(.env의 STOCKEASY_COOKIE 사용) "
            "반환값: [{code, name, rs_score, sector}] 형식의 종목 리스트."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "filter_candidates",
        "description": (
            "RS 점수 기준으로 후보군을 필터링합니다. "
            "threshold 이상인 종목만 남기고 상위 max_count개를 반환합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "stocks": {
                    "type": "array",
                    "description": "fetch_rs_ranking 결과 종목 리스트",
                    "items": {"type": "object"},
                },
                "threshold": {
                    "type": "number",
                    "description": f"RS 최소 점수 (기본: {config.RS_THRESHOLD})",
                },
                "max_count": {
                    "type": "integer",
                    "description": f"최대 종목 수 (기본: {config.MAX_FIRST_CANDIDATES})",
                },
            },
            "required": ["stocks"],
        },
    },
    {
        "name": "save_first_stage",
        "description": "1차 후보군을 오늘 날짜로 저장합니다. 저장 경로를 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "description": "저장할 1차 후보군 리스트",
                    "items": {"type": "object"},
                },
            },
            "required": ["candidates"],
        },
    },
]


# ──────────────────────────────────────────
# 도구 실행 함수
# ──────────────────────────────────────────
async def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Claude가 요청한 도구를 실제 실행하고 결과를 문자열로 반환"""

    if tool_name == "fetch_rs_ranking":
        stocks = run_collection()  # 동기 함수
        return json.dumps({"stocks": stocks, "count": len(stocks)}, ensure_ascii=False)

    elif tool_name == "filter_candidates":
        stocks = tool_input.get("stocks", [])
        threshold = tool_input.get("threshold", config.RS_THRESHOLD)
        max_count = tool_input.get("max_count", config.MAX_FIRST_CANDIDATES)

        filtered = [s for s in stocks if s.get("rs_score", 0) >= threshold]
        filtered.sort(key=lambda x: x["rs_score"], reverse=True)
        result = filtered[:max_count]
        return json.dumps({
            "filtered_count": len(result),
            "original_count": len(stocks),
            "candidates": result,
        }, ensure_ascii=False)

    elif tool_name == "save_first_stage":
        candidates = tool_input.get("candidates", [])
        date_str = today_str()
        path = save_candidates(date_str, stage=1, candidates=candidates)
        return json.dumps({"saved_path": path, "count": len(candidates), "date": date_str})

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ──────────────────────────────────────────
# Agent 메인 루프
# ──────────────────────────────────────────
class DataCollectorAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL

    async def run(self) -> list[dict]:
        """
        1차 후보군 선정 실행

        Returns:
            1차 후보군 종목 리스트. 실패 시 빈 리스트.
        """
        print("[DataCollector] Agent 시작")

        system_prompt = (
            "당신은 한국 주식 시장 데이터 수집 전문가입니다. "
            "주어진 도구를 순서대로 사용하여 RS(상대강도) 상위 종목을 수집하고 "
            "1차 후보군을 선정하세요.\n\n"
            "실행 순서:\n"
            "1. fetch_rs_ranking으로 RS 랭킹 데이터 수집\n"
            "2. filter_candidates로 RS 점수 기준 필터링\n"
            "3. save_first_stage로 결과 저장\n"
            "4. 최종 후보군 요약 리포트 출력"
        )

        user_message = (
            f"오늘({today_str()}) 한국 주식 RS 상위 종목을 수집하여 1차 후보군을 선정하세요.\n"
            f"기준: RS 점수 {config.RS_THRESHOLD} 이상, 상위 {config.MAX_FIRST_CANDIDATES}개"
        )

        messages = [{"role": "user", "content": user_message}]
        first_stage_candidates: list[dict] = []

        # Agentic loop
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            # 응답을 대화 히스토리에 추가
            messages.append({"role": "assistant", "content": response.content})

            # 종료 조건
            if response.stop_reason == "end_turn":
                print("[DataCollector] Agent 완료")
                # 마지막 텍스트 출력
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"[DataCollector] {block.text}")
                break

            # 도구 호출 처리
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    print(f"[DataCollector] 도구 실행: {block.name}")
                    result_str = await _execute_tool(block.name, block.input)
                    result_data = json.loads(result_str)

                    # 1차 후보군 캡처
                    if block.name == "save_first_stage":
                        pass  # 저장은 data_store에서 처리
                    if block.name == "filter_candidates" and "candidates" in result_data:
                        first_stage_candidates = result_data["candidates"]

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

                messages.append({"role": "user", "content": tool_results})
            else:
                # 예상치 못한 stop_reason
                break

        print(f"[DataCollector] 1차 후보군: {len(first_stage_candidates)}개")
        return first_stage_candidates


# 직접 실행 시 테스트
if __name__ == "__main__":
    agent = DataCollectorAgent()
    result = asyncio.run(agent.run())
    print(f"\n1차 후보군 {len(result)}개:")
    for r in result[:5]:
        print(r)
