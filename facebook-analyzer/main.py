#!/usr/bin/env python3
"""
Facebook Analyzer - CLI 진입점

사용법:
  python main.py --init          전체 히스토리 수집 및 분석 (최초 1회 실행)
  python main.py --daily         오늘 게시물 수집 및 분석 (매일 자동 실행)
  python main.py --report        마스터 인사이트 재생성 (저장된 데이터 기반)
  python main.py --add           게시물 수동 입력 (개인 프로필 등 API 불가 시)
  python main.py --view DATE     특정 날짜 리포트 출력 (예: --view 2026-03-18)
  python main.py --list          저장된 날짜 목록 출력

필수 환경변수 (setx로 설정 후 터미널 재시작):
  ANTHROPIC_API_KEY
  FB_PAGE_ID
  FB_ACCESS_TOKEN
"""

import argparse
import sys
from datetime import datetime, timezone

from config import validate_env, ensure_dirs
from facebook_crawler import FacebookCrawler, manual_post_entry
from analyzer import PostAnalyzer
from storage import (
    save_daily_report,
    load_all_posts,
    get_existing_dates,
    save_master_insights,
    load_master_insights,
    load_daily_report,
    list_all_report_dates,
)


# ── 명령 함수들 ──────────────────────────────────────────────────────────────

def cmd_init(crawler: FacebookCrawler, analyzer: PostAnalyzer):
    """전체 히스토리를 수집하고 날짜별로 분석한다."""
    print("[STEP 1] 전체 히스토리 수집 중 (수분 소요될 수 있음)...")
    all_posts = crawler.fetch_all_history()

    if not all_posts:
        print("        수집된 게시물이 없습니다.")
        print("        페이지 ID와 액세스 토큰을 확인하거나 --add 로 수동 입력하세요.")
        return

    # 날짜별로 그룹핑
    by_date: dict = {}
    for post in all_posts:
        date_str = post["created_at"][:10]  # "YYYY-MM-DD"
        by_date.setdefault(date_str, []).append(post)

    existing = get_existing_dates()
    new_dates = sorted(set(by_date.keys()) - existing)
    print(f"        새로운 날짜 {len(new_dates)}개 처리 예정 (기존 {len(existing)}개 건너뜀)")

    for i, date_str in enumerate(new_dates, 1):
        posts = by_date[date_str]
        print(f"[STEP 2] [{i}/{len(new_dates)}] {date_str} 분석 중 ({len(posts)}개 게시물)...")
        analyses = [analyzer.analyze_post(p) for p in posts]
        summary  = analyzer.daily_summary(posts, date_str)
        save_daily_report(date_str, posts, summary, analyses)

    print("[STEP 3] 마스터 인사이트 생성 중...")
    _run_report(analyzer)
    print("\n[완료] --init 작업이 끝났습니다.")
    print(f"       저장 위치: reports/daily/ ({len(new_dates)}개 파일)")


def cmd_daily(crawler: FacebookCrawler, analyzer: PostAnalyzer):
    """오늘 게시물을 수집하고 분석한다."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[STEP 1] {today} 게시물 수집 중...")
    posts = crawler.fetch_today()

    if not posts:
        print(f"        오늘({today}) 게시물이 없습니다.")
        return

    print(f"        {len(posts)}개 게시물 발견")
    print("[STEP 2] 게시물 분석 중...")
    analyses = [analyzer.analyze_post(p) for p in posts]
    summary  = analyzer.daily_summary(posts, today)
    save_daily_report(today, posts, summary, analyses)

    print("[STEP 3] 마스터 인사이트 업데이트 중...")
    _run_report(analyzer)
    print(f"\n[완료] {today} 일간 분석이 완료되었습니다.")


def _run_report(analyzer: PostAnalyzer):
    """저장된 모든 게시물을 바탕으로 마스터 인사이트를 재생성한다."""
    all_posts = load_all_posts()
    if not all_posts:
        print("        저장된 게시물이 없습니다. --init 또는 --add 를 먼저 실행하세요.")
        return

    # 최대 500개 게시물 텍스트를 인사이트 프롬프트에 사용 (컨텍스트 제한 고려)
    posts_text = "\n\n".join(
        f"[{p['created_at'][:10]}] {p['message'][:600]}"
        for p in all_posts[-500:]
    )
    existing = load_master_insights()
    insights = analyzer.update_insights(posts_text, existing)
    save_master_insights(insights)


def cmd_report(analyzer: PostAnalyzer):
    """마스터 인사이트를 재생성한다 (--report 명령)."""
    print("[STEP 1] 저장된 모든 게시물 로드 중...")
    _run_report(analyzer)
    print("\n[완료] 마스터 인사이트가 업데이트되었습니다.")
    print("       저장 위치: reports/insights/master-insights.md")


def cmd_add(analyzer: PostAnalyzer):
    """게시물을 수동으로 입력하고 분석한다."""
    try:
        post = manual_post_entry()
    except KeyboardInterrupt:
        print("\n취소되었습니다.")
        return

    date_str = post["created_at"][:10]
    print(f"\n[STEP 1] {date_str} 게시물 분석 중...")
    analysis = analyzer.analyze_post(post)
    summary  = analyzer.daily_summary([post], date_str)
    save_daily_report(date_str, [post], summary, [analysis])

    print("[STEP 2] 마스터 인사이트 업데이트 중...")
    _run_report(analyzer)
    print(f"\n[완료] 게시물이 {date_str}.md 에 저장되었습니다.")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Facebook 페이지 게시물 크롤러 & Claude AI 분석기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init",   action="store_true", help="전체 히스토리 수집·분석")
    group.add_argument("--daily",  action="store_true", help="오늘 게시물 수집·분석")
    group.add_argument("--report", action="store_true", help="마스터 인사이트 재생성")
    group.add_argument("--add",    action="store_true", help="게시물 수동 입력")
    group.add_argument("--view",   metavar="DATE",      help="특정 날짜 리포트 출력 (YYYY-MM-DD)")
    group.add_argument("--list",   action="store_true", help="저장된 날짜 목록 출력")
    args = parser.parse_args()

    # --list, --view 는 API 없이 동작
    if args.list:
        dates = list_all_report_dates()
        if not dates:
            print("저장된 리포트가 없습니다.")
        else:
            print(f"저장된 리포트 ({len(dates)}개):")
            for d in dates:
                print(f"  {d}")
        return

    if args.view:
        content = load_daily_report(args.view)
        if content:
            print(content)
        else:
            print(f"[오류] {args.view} 날짜의 리포트가 없습니다.")
            dates = list_all_report_dates()
            if dates:
                print(f"       최근 날짜: {dates[-1]}")
        return

    # 나머지 명령은 환경변수 필요
    cfg = validate_env()
    ensure_dirs()

    analyzer = PostAnalyzer(cfg["anthropic_key"])

    if args.add:
        cmd_add(analyzer)
        return

    # 크롤러가 필요한 명령
    crawler = FacebookCrawler(cfg["page_id"], cfg["access_token"])

    if args.init:   cmd_init(crawler, analyzer)
    elif args.daily: cmd_daily(crawler, analyzer)
    elif args.report: cmd_report(analyzer)


if __name__ == "__main__":
    main()
