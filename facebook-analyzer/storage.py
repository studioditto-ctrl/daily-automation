#!/usr/bin/env python3
"""
Facebook Analyzer - 저장소 모듈

파일 구조:
  reports/daily/YYYY-MM-DD.md    날짜별 게시물 분석 (마크다운, 사람이 읽는 형태)
  reports/daily/YYYY-MM-DD.json  날짜별 원본 게시물 데이터 (재처리용)
  reports/insights/master-insights.md  전체 기간 종합 인사이트
"""

import json
from datetime import datetime
from pathlib import Path

from config import DAILY_DIR, MASTER_INSIGHTS_FILE


def _daily_md_path(date_str: str) -> Path:
    return DAILY_DIR / f"{date_str}.md"


def _daily_json_path(date_str: str) -> Path:
    return DAILY_DIR / f"{date_str}.json"


def save_daily_report(date_str: str, posts: list, summary: str, analyses: list):
    """
    하루치 게시물 분석을 마크다운(.md)과 원본 JSON(.json)으로 저장한다.
    이미 파일이 존재하면 덮어쓴다.
    """
    md_path   = _daily_md_path(date_str)
    json_path = _daily_json_path(date_str)

    # ── 마크다운 생성 ─────────────────────────────────────────────────────────
    lines = [
        f"# Facebook Posts — {date_str}\n\n",
        f"_수집일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_  \n",
        f"_게시물 수: {len(posts)}개_\n\n",
        "---\n\n",
        "## 일간 요약\n\n",
        summary.strip(),
        "\n\n---\n\n",
        "## 개별 게시물 분석\n\n",
    ]

    for i, post in enumerate(posts, 1):
        analysis = analyses[i - 1] if i - 1 < len(analyses) else {}

        lines.append(f"### 게시물 {i}\n\n")
        lines.append(f"**날짜**: {post.get('created_at', 'N/A')}  \n")

        if post.get("url"):
            lines.append(f"**링크**: [{post['url']}]({post['url']})  \n")

        lines.append(f"\n{post.get('message', '').strip()}\n\n")

        if analysis.get("analysis_raw"):
            lines.append("**분석 결과**:\n\n")
            lines.append(analysis["analysis_raw"].strip())
            lines.append("\n\n")

        lines.append("---\n\n")

    md_path.write_text("".join(lines), encoding="utf-8")

    # ── 원본 JSON 저장 (재처리 시 API 재호출 없이 사용) ──────────────────────
    json_path.write_text(
        json.dumps(posts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"        저장됨: {md_path.name}")


def load_all_posts() -> list:
    """저장된 모든 날짜의 JSON 파일을 읽어 게시물 리스트를 반환한다 (날짜 오름차순)."""
    all_posts = []
    for json_file in sorted(DAILY_DIR.glob("*.json")):
        try:
            posts = json.loads(json_file.read_text(encoding="utf-8"))
            all_posts.extend(posts)
        except (json.JSONDecodeError, OSError):
            print(f"        [경고] 파일 읽기 실패: {json_file.name}")
    return all_posts


def get_existing_dates() -> set:
    """이미 마크다운 리포트가 있는 날짜 집합(YYYY-MM-DD)을 반환한다."""
    return {f.stem for f in DAILY_DIR.glob("*.md")}


def save_master_insights(content: str):
    """마스터 인사이트 파일을 저장한다."""
    MASTER_INSIGHTS_FILE.write_text(content, encoding="utf-8")
    print(f"        인사이트 저장됨: {MASTER_INSIGHTS_FILE.name}")


def load_master_insights() -> str:
    """마스터 인사이트 파일을 읽어 반환한다. 없으면 빈 문자열."""
    if MASTER_INSIGHTS_FILE.exists():
        return MASTER_INSIGHTS_FILE.read_text(encoding="utf-8")
    return ""


def load_daily_report(date_str: str) -> str:
    """특정 날짜의 마크다운 리포트를 읽어 반환한다. 없으면 빈 문자열."""
    path = _daily_md_path(date_str)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def list_all_report_dates() -> list:
    """저장된 모든 날짜 문자열을 정렬하여 반환한다."""
    return sorted(f.stem for f in DAILY_DIR.glob("*.md"))
