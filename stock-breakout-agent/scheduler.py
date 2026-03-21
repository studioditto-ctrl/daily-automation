"""
APScheduler 기반 로컬 자동 실행

실행 시각: 평일 15:30 KST (장 마감 후)
사용법:
  python scheduler.py          # 스케줄러 시작 (백그라운드 대기)
  python scheduler.py --now    # 즉시 1회 실행 (테스트용)
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from agents.orchestrator import run_daily

KST = pytz.timezone("Asia/Seoul")


async def scheduled_job():
    """스케줄러가 호출하는 진입점"""
    print("[Scheduler] 예약 실행 시작")
    await run_daily()


def main():
    run_now = "--now" in sys.argv

    if run_now:
        print("[Scheduler] 즉시 실행 모드")
        asyncio.run(run_daily())
        return

    scheduler = AsyncIOScheduler(timezone=KST)

    # 평일(월~금) 15:30 KST 실행
    scheduler.add_job(
        scheduled_job,
        CronTrigger(
            day_of_week="mon-fri",
            hour=15,
            minute=30,
            timezone=KST,
        ),
        id="daily_breakout",
        name="돌파매매 후보군 일일 분석",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] 시작됨 — 평일 15:30 KST 자동 실행")
    print("[Scheduler] 즉시 실행하려면: python scheduler.py --now")
    print("[Scheduler] 중지: Ctrl+C")

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("[Scheduler] 종료")


if __name__ == "__main__":
    main()
