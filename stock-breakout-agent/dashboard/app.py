"""
웹 대시보드 — FastAPI 서버

엔드포인트:
  GET /                        메인 대시보드 (오늘 2차 후보군)
  GET /history                 날짜별 결과 목록
  GET /candidates/{date}       특정 날짜 1차/2차 후보군 상세
  GET /api/candidates          JSON API (오늘 또는 date 쿼리)
  POST /api/run                수동 파이프라인 실행 트리거
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from storage.data_store import load_candidates, list_dates, today_str

app = FastAPI(title="주식 돌파매매 대시보드", version="1.0.0")

# 정적 파일 / 템플릿
_BASE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_BASE, "templates"))

# 파이프라인 실행 상태 (단순 in-memory)
_pipeline_status = {"running": False, "last_run": None, "last_result": None}


def _naver_chart_url(code: str) -> str:
    return f"https://finance.naver.com/item/main.naver?code={code}"


def _load_page_data(date_str: str) -> dict:
    """특정 날짜의 1차/2차 후보군 데이터 로드"""
    stage1 = load_candidates(date_str, stage=1) or {}
    stage2 = load_candidates(date_str, stage=2) or {}

    first  = stage1.get("candidates", [])
    second = stage2.get("candidates", [])

    # 네이버 차트 링크 추가
    for s in second:
        s["chart_url"] = _naver_chart_url(s.get("code", ""))

    return {
        "date": date_str,
        "saved_at": stage2.get("saved_at", ""),
        "first_count": len(first),
        "second_count": len(second),
        "first_stage": first,
        "second_stage": second,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    date_str = today_str()
    data = _load_page_data(date_str)
    dates = list_dates()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": data,
        "dates": dates,
        "pipeline_status": _pipeline_status,
        "current_date": date_str,
    })


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    dates = list_dates()
    summaries = []
    for d in dates:
        s1 = load_candidates(d, 1) or {}
        s2 = load_candidates(d, 2) or {}
        summaries.append({
            "date": d,
            "first_count": s1.get("count", 0),
            "second_count": s2.get("count", 0),
            "saved_at": s2.get("saved_at", ""),
        })
    return templates.TemplateResponse("history.html", {
        "request": request,
        "summaries": summaries,
    })


@app.get("/candidates/{date_str}", response_class=HTMLResponse)
async def candidates_detail(request: Request, date_str: str):
    data = _load_page_data(date_str)
    dates = list_dates()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": data,
        "dates": dates,
        "pipeline_status": _pipeline_status,
        "current_date": date_str,
    })


@app.get("/api/candidates")
async def api_candidates(date: str = None):
    date_str = date or today_str()
    data = _load_page_data(date_str)
    return JSONResponse(content=data)


@app.post("/api/run")
async def api_run(background_tasks: BackgroundTasks):
    """파이프라인 수동 실행 (백그라운드)"""
    if _pipeline_status["running"]:
        return JSONResponse(content={"status": "already_running"}, status_code=409)

    async def _run():
        _pipeline_status["running"] = True
        _pipeline_status["last_run"] = datetime.now().isoformat()
        try:
            from agents.orchestrator import run_daily
            result = await run_daily()
            _pipeline_status["last_result"] = {
                "first_count": len(result.get("first_stage", [])),
                "second_count": len(result.get("second_stage", [])),
                "elapsed": result.get("elapsed_seconds"),
            }
        except Exception as e:
            _pipeline_status["last_result"] = {"error": str(e)}
        finally:
            _pipeline_status["running"] = False

    background_tasks.add_task(_run)
    return JSONResponse(content={"status": "started"})


@app.get("/api/status")
async def api_status():
    return JSONResponse(content=_pipeline_status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=config.DASHBOARD_PORT, reload=True)
