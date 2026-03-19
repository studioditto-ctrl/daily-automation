#!/usr/bin/env python3
"""
Facebook Analyzer - 일간 자동 실행 스케줄러 (APScheduler 방식)

매일 오전 9시에 --daily 명령을 자동 실행한다.

사용법:
  python scheduler.py          백그라운드에서 상시 실행 (Ctrl+C로 중지)

권장: Windows 작업 스케줄러를 사용하는 것이 더 안정적이다.
  setup_scheduler.bat 파일을 관리자 권한으로 실행하면 자동 등록된다.

참고:
  - APScheduler는 이 프로세스가 실행 중이어야 동작
  - Windows 작업 스케줄러는 시스템이 켜져 있으면 독립적으로 동작
"""

import subprocess
import sys
import logging
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SCRIPT_DIR  = Path(__file__).parent
MAIN_SCRIPT = SCRIPT_DIR / "main.py"
RUN_HOUR    = 9    # 실행 시각 (24시간제)
RUN_MINUTE  = 0


def run_daily_job():
    logging.info("--daily 작업 시작...")
    result = subprocess.run(
        [sys.executable, str(MAIN_SCRIPT), "--daily"],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        logging.info(result.stdout.strip())
    if result.returncode != 0:
        logging.error(f"오류 발생 (returncode={result.returncode}):")
        logging.error(result.stderr.strip())
    else:
        logging.info("--daily 작업 완료.")


def main():
    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        run_daily_job,
        trigger=CronTrigger(hour=RUN_HOUR, minute=RUN_MINUTE),
        id="daily_facebook_analyzer",
        name="Facebook 일간 분석",
        misfire_grace_time=3600,  # 1시간 이내 누락이면 즉시 실행
    )

    logging.info(f"스케줄러 시작. 매일 {RUN_HOUR:02d}:{RUN_MINUTE:02d} (KST)에 실행됩니다.")
    logging.info("Ctrl+C로 중지하세요.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logging.info("스케줄러 중지됨.")


if __name__ == "__main__":
    main()
