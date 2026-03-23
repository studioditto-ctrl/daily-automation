"""대시보드 실행 진입점 — 프로젝트 루트에서 실행"""
import os
import sys

# stock-breakout-agent 디렉토리를 sys.path에 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

import uvicorn
import config

if __name__ == "__main__":
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=config.DASHBOARD_PORT, reload=True)
