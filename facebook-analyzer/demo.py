#!/usr/bin/env python3
"""
Facebook Analyzer - 데모 스크립트
실제 Facebook API 없이 샘플 게시물로 전체 파이프라인을 시연한다.
"""

import os
import sys
from pathlib import Path

# 데모용 샘플 게시물 (유명 사상가 스타일)
SAMPLE_POSTS = [
    {
        "id": "demo_001",
        "message": "대부분의 사람들은 '완벽한 타이밍'을 기다리다 아무것도 시작하지 못합니다.\n\n진실은 이렇습니다: 완벽한 타이밍은 존재하지 않습니다.\n\n지금 이 순간이 당신이 가진 유일한 시간입니다.\n\n불완전하게 시작하는 것이 완벽하게 기다리는 것보다 항상 낫습니다.",
        "created_at": "2026-03-17T08:30:00+0000",
        "url": "https://facebook.com/demo/posts/001",
        "image_url": "",
        "attachments": []
    },
    {
        "id": "demo_002",
        "message": "오늘 한 가지를 깨달았습니다.\n\n성공한 사람들은 특별한 재능을 가진 게 아닙니다.\n그들은 단지 실패했을 때 포기하지 않았을 뿐입니다.\n\n실패는 끝이 아닙니다. 실패는 방향을 바꾸라는 신호입니다.\n\n오늘 당신이 직면한 어려움은 내일의 당신을 만드는 재료입니다.",
        "created_at": "2026-03-17T19:00:00+0000",
        "url": "https://facebook.com/demo/posts/002",
        "image_url": "",
        "attachments": []
    },
    {
        "id": "demo_003",
        "message": "리더십에 대한 가장 큰 오해:\n\n많은 사람들이 리더는 가장 큰 목소리를 가진 사람이라고 생각합니다.\n\n하지만 제가 수십 년간 관찰한 진짜 리더들은 다릅니다:\n- 가장 먼저 듣는 사람\n- 가장 늦게 말하는 사람\n- 공을 팀에게 돌리는 사람\n\n진정한 리더십은 권위에서 오지 않습니다. 신뢰에서 옵니다.",
        "created_at": "2026-03-18T09:00:00+0000",
        "url": "https://facebook.com/demo/posts/003",
        "image_url": "",
        "attachments": []
    },
    {
        "id": "demo_004",
        "message": "습관의 힘을 과소평가하지 마세요.\n\n매일 1%씩 나아진다면, 1년 후엔 37배 성장합니다.\n매일 1%씩 퇴보한다면, 1년 후엔 거의 0에 가까워집니다.\n\n오늘 하루의 선택들이 1년 후의 당신을 만듭니다.\n\n지금 당장 크게 변할 필요 없습니다. 그냥 오늘 조금 더 잘하면 됩니다.",
        "created_at": "2026-03-18T20:00:00+0000",
        "url": "https://facebook.com/demo/posts/004",
        "image_url": "",
        "attachments": []
    },
    {
        "id": "demo_005",
        "message": "오늘 아침 일출을 보며 생각했습니다.\n\n우리는 너무 많은 시간을 '나중에'에 투자합니다.\n나중에 행복할 거야. 나중에 시작할 거야. 나중에 사랑한다고 말할 거야.\n\n태양은 매일 약속 없이 떠오릅니다.\n당신은 오늘 무엇을 나중으로 미루고 있나요?\n\n지금 시작하세요. 지금 말하세요. 지금 살아가세요.",
        "created_at": "2026-03-19T07:00:00+0000",
        "url": "https://facebook.com/demo/posts/005",
        "image_url": "",
        "attachments": []
    },
]


def run_demo():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        print("       setx ANTHROPIC_API_KEY \"sk-ant-...\" 후 터미널 재시작")
        sys.exit(1)

    # 데모 리포트 저장 경로
    demo_dir = Path(__file__).parent / "reports" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    from analyzer import PostAnalyzer
    from storage import save_daily_report, save_master_insights

    analyzer = PostAnalyzer(api_key)

    # 날짜별 그룹핑
    by_date: dict = {}
    for post in SAMPLE_POSTS:
        date_str = post["created_at"][:10]
        by_date.setdefault(date_str, []).append(post)

    print("=" * 60)
    print("  Facebook Analyzer 데모")
    print(f"  샘플 게시물 {len(SAMPLE_POSTS)}개 / {len(by_date)}일치")
    print("=" * 60)

    saved_files = []

    for date_str, posts in sorted(by_date.items()):
        print(f"\n[{date_str}] {len(posts)}개 게시물 분석 중...")

        analyses = []
        for i, post in enumerate(posts, 1):
            print(f"  게시물 {i}/{len(posts)} 분석...")
            analysis = analyzer.analyze_post(post)
            analyses.append(analysis)

        print(f"  일간 요약 생성 중...")
        summary = analyzer.daily_summary(posts, date_str)

        # 데모용 경로에 저장
        from config import DAILY_DIR
        import json
        md_path   = demo_dir / f"{date_str}.md"
        json_path = demo_dir / f"{date_str}.json"

        lines = [
            f"# Facebook Posts (DEMO) — {date_str}\n\n",
            f"_게시물 수: {len(posts)}개_\n\n---\n\n",
            "## 일간 요약\n\n",
            summary.strip(),
            "\n\n---\n\n## 개별 게시물 분석\n\n",
        ]
        for i, (post, analysis) in enumerate(zip(posts, analyses), 1):
            lines.append(f"### 게시물 {i}\n\n")
            lines.append(f"**날짜**: {post['created_at']}  \n")
            lines.append(f"\n{post['message'].strip()}\n\n")
            lines.append("**분석 결과**:\n\n")
            lines.append(analysis["analysis_raw"].strip())
            lines.append("\n\n---\n\n")

        md_path.write_text("".join(lines), encoding="utf-8")
        json_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        saved_files.append(md_path)
        print(f"  저장: {md_path.name}")

    # 마스터 인사이트 생성
    print("\n[마스터 인사이트] 전체 패턴 분석 중...")
    all_text = "\n\n".join(
        f"[{p['created_at'][:10]}] {p['message']}"
        for p in SAMPLE_POSTS
    )
    insights = analyzer.update_insights(all_text, "")
    insights_path = demo_dir / "master-insights.md"
    insights_path.write_text(insights, encoding="utf-8")

    print("\n" + "=" * 60)
    print("  데모 완료!")
    print("=" * 60)
    print(f"\n생성된 파일:")
    for f in saved_files:
        size = f.stat().st_size
        print(f"  {f.name}  ({size:,} bytes)")
    print(f"  master-insights.md  ({insights_path.stat().st_size:,} bytes)")
    print(f"\n저장 위치: {demo_dir}")

    # 미리보기 출력
    print("\n" + "─" * 60)
    print("  [마스터 인사이트 미리보기]")
    print("─" * 60)
    preview = insights_path.read_text(encoding="utf-8")
    print(preview[:1200])
    if len(preview) > 1200:
        print(f"\n  ... (총 {len(preview):,}자, 전체 내용은 파일에서 확인)")


if __name__ == "__main__":
    run_demo()
