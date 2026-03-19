#!/usr/bin/env python3
"""
Facebook Analyzer - Graph API 크롤러

공개 Facebook 페이지의 게시물을 가져온다.
Graph API 엔드포인트: GET /v18.0/{page_id}/posts

수집 필드:
  id, message, story, created_time, permalink_url, full_picture, attachments

Rate Limit:
  - 표준 등급: 시간당 약 200회 호출
  - 요청 간 0.5초 딜레이로 여유 있게 유지

개인 프로필 대상인 경우:
  Graph API 접근 불가 → manual_post_entry() 를 통해 수동 입력 후
  동일한 분석 파이프라인 사용
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional
import requests

from config import GRAPH_API_BASE, MAX_POSTS_PER_REQUEST, MAX_HISTORY_PAGES, REQUEST_DELAY_SEC

# 수집할 필드 목록
FIELDS = (
    "id,message,story,created_time,permalink_url,"
    "full_picture,attachments{title,description,url}"
)


class FacebookCrawler:
    def __init__(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.token   = access_token
        self.base_url = f"{GRAPH_API_BASE}/{page_id}/posts"

    def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """Graph API GET 요청. 실패 시 예외를 발생시킨다."""
        p = params or {}
        p["access_token"] = self.token
        r = requests.get(url, params=p, timeout=20)
        r.raise_for_status()
        return r.json()

    def fetch_since(self, since_dt: datetime, until_dt: Optional[datetime] = None) -> list:
        """
        since_dt ~ until_dt 사이의 게시물을 모두 가져온다.
        until_dt 기본값: 현재 시각
        반환: 정규화된 게시물 딕셔너리 리스트
        """
        since_ts = int(since_dt.replace(tzinfo=timezone.utc).timestamp())
        until_ts = int(
            (until_dt or datetime.now(timezone.utc)).timestamp()
        )

        params = {
            "fields": FIELDS,
            "limit":  MAX_POSTS_PER_REQUEST,
            "since":  since_ts,
            "until":  until_ts,
        }

        all_posts = []
        url = self.base_url
        page_count = 0

        while url and page_count < MAX_HISTORY_PAGES:
            print(f"        [API] 페이지 {page_count + 1} 수집 중...")
            try:
                data = self._get(url, params if page_count == 0 else None)
            except requests.HTTPError as e:
                print(f"        [오류] API 호출 실패: {e}")
                break

            posts = data.get("data", [])
            for p in posts:
                # message 필드가 있는 게시물만 처리 (자동생성 story 제외)
                if p.get("message"):
                    all_posts.append(self._normalize(p))

            # 다음 페이지 URL (cursor-based pagination)
            paging = data.get("paging", {})
            url = paging.get("next")  # 마지막 페이지면 None
            params = None  # next URL에 이미 모든 파라미터가 인코딩되어 있음
            page_count += 1

            if url:
                time.sleep(REQUEST_DELAY_SEC)

        print(f"        총 {len(all_posts)}개 게시물 수집 완료")
        return all_posts

    def fetch_today(self) -> list:
        """오늘(UTC 기준) 게시된 게시물을 가져온다."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return self.fetch_since(today_start)

    def fetch_date(self, date_str: str) -> list:
        """특정 날짜(YYYY-MM-DD)의 게시물을 가져온다."""
        start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end   = start + timedelta(days=1)
        return self.fetch_since(start, end)

    def fetch_all_history(self) -> list:
        """
        최대 2년치 히스토리를 가져온다.
        Graph API는 보통 최근 2년 데이터를 제공한다.
        """
        two_years_ago = datetime.now(timezone.utc) - timedelta(days=730)
        return self.fetch_since(two_years_ago)

    @staticmethod
    def _normalize(post: dict) -> dict:
        """Graph API 원본 게시물을 정제된 딕셔너리로 변환한다."""
        return {
            "id":          post["id"],
            "message":     post.get("message", post.get("story", "")).strip(),
            "created_at":  post.get("created_time", ""),  # ISO 8601
            "url":         post.get("permalink_url", ""),
            "image_url":   post.get("full_picture", ""),
            "attachments": _extract_attachments(post),
        }


def _extract_attachments(post: dict) -> list:
    """게시물의 첨부파일 정보를 추출한다."""
    raw = post.get("attachments", {}).get("data", [])
    return [
        {"title": a.get("title", ""), "url": a.get("url", "")}
        for a in raw
    ]


# ── 수동 입력 모드 (개인 프로필 등 API 접근 불가 시) ─────────────────────────

def manual_post_entry() -> dict:
    """
    CLI 대화형 입력으로 게시물 데이터를 수동으로 생성한다.
    개인 프로필 등 API 접근이 불가한 경우 사용.
    """
    print("\n[수동 입력] 게시물 정보를 입력하세요 (Ctrl+C로 취소):")
    print("  (여러 줄 입력 시 빈 줄에서 Enter를 두 번 누르세요)")

    # 여러 줄 텍스트 입력
    print("  게시물 내용:")
    lines = []
    while True:
        line = input("  > ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    message = "\n".join(lines).strip()

    date_input = input("  게시일 (YYYY-MM-DD, 비워두면 오늘): ").strip()
    if not date_input:
        date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000")
    else:
        date_str = f"{date_input}T00:00:00+0000"

    url = input("  게시물 URL (없으면 Enter): ").strip()

    return {
        "id":          f"manual_{int(time.time())}",
        "message":     message,
        "created_at":  date_str,
        "url":         url,
        "image_url":   "",
        "attachments": [],
    }
