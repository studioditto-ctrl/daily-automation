#!/usr/bin/env python3
"""
Facebook Analyzer - 토큰 검증 & 페이지 ID 확인 도우미 (최초 1회 실행)

실행 전 설정:
  set FB_APP_ID=앱ID
  set FB_APP_SECRET=앱시크릿
  set FB_PAGE_NAME=페이지사용자명(또는_숫자ID)

또는 이미 토큰이 있다면:
  set FB_ACCESS_TOKEN=기존_토큰
  set FB_PAGE_NAME=페이지사용자명

사용법:
  python setup_token.py

출력에서 'id' 값을 복사하여:
  setx FB_PAGE_ID "출력된_숫자_ID"
  setx FB_ACCESS_TOKEN "출력된_토큰"
"""

import os
import requests
import json

GRAPH_BASE = "https://graph.facebook.com/v18.0"


def get_app_token(app_id: str, app_secret: str) -> str:
    """App Access Token 발급 (만료 없음, 공개 페이지 읽기용)."""
    print("[STEP 1] App Access Token 발급 중...")
    url = f"{GRAPH_BASE}/oauth/access_token"
    r = requests.get(url, params={
        "client_id":     app_id,
        "client_secret": app_secret,
        "grant_type":    "client_credentials",
    }, timeout=10)
    r.raise_for_status()
    token = r.json().get("access_token", "")
    print(f"        토큰 발급 완료: {token[:20]}...")
    return token


def debug_token(token: str) -> dict:
    """토큰 유효성 및 만료일 확인."""
    print("[STEP 2] 토큰 유효성 확인 중...")
    r = requests.get(f"{GRAPH_BASE}/debug_token", params={
        "input_token":  token,
        "access_token": token,
    }, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", {})
    print(f"        유효: {data.get('is_valid', False)}")
    print(f"        앱 ID: {data.get('app_id', 'N/A')}")
    print(f"        만료: {data.get('expires_at', '만료 없음(앱 토큰)')}")
    return data


def find_page(page_name: str, token: str) -> dict:
    """페이지 이름으로 페이지 ID, 이름, 팬 수를 조회한다."""
    print(f"[STEP 3] 페이지 정보 조회 중: {page_name}")
    r = requests.get(f"{GRAPH_BASE}/{page_name}", params={
        "fields":       "id,name,fan_count,about",
        "access_token": token,
    }, timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"        페이지 이름: {data.get('name', 'N/A')}")
    print(f"        페이지 ID:   {data.get('id', 'N/A')}")
    print(f"        팬/팔로워:   {data.get('fan_count', 'N/A'):,}명")
    return data


def test_posts(page_id: str, token: str):
    """게시물 1개를 테스트로 가져온다."""
    print(f"[STEP 4] 게시물 접근 테스트 중...")
    r = requests.get(f"{GRAPH_BASE}/{page_id}/posts", params={
        "fields":       "id,message,created_time",
        "limit":        1,
        "access_token": token,
    }, timeout=10)
    r.raise_for_status()
    data = r.json()
    posts = data.get("data", [])
    if posts:
        p = posts[0]
        print(f"        최근 게시물 날짜: {p.get('created_time', 'N/A')}")
        msg = p.get('message', '(메시지 없음)')[:80]
        print(f"        내용 미리보기: {msg}...")
        print(f"\n        ✅ 게시물 접근 성공! API 연결이 정상입니다.")
    else:
        print(f"        ⚠️  게시물이 없거나 접근 권한이 없습니다.")
        print(f"           페이지가 공개 상태인지 확인하세요.")


def main():
    # 기존 토큰 또는 앱 자격증명으로 토큰 발급
    token = os.environ.get("FB_ACCESS_TOKEN", "")

    if not token:
        app_id     = os.environ.get("FB_APP_ID", "")
        app_secret = os.environ.get("FB_APP_SECRET", "")
        if not app_id or not app_secret:
            print("[오류] 다음 중 하나를 설정해야 합니다:")
            print("  set FB_ACCESS_TOKEN=기존토큰")
            print("  또는")
            print("  set FB_APP_ID=앱ID")
            print("  set FB_APP_SECRET=앱시크릿")
            raise SystemExit(1)
        token = get_app_token(app_id, app_secret)
    else:
        print(f"[STEP 1] 기존 토큰 사용: {token[:20]}...")

    # 토큰 검증
    try:
        debug_token(token)
    except Exception as e:
        print(f"        [경고] 토큰 검증 실패: {e}")

    # 페이지 조회
    page_name = os.environ.get("FB_PAGE_NAME", "")
    if not page_name:
        print("\n[오류] FB_PAGE_NAME 환경변수를 설정하세요:")
        print("  set FB_PAGE_NAME=페이지사용자명")
        raise SystemExit(1)

    try:
        page_data = find_page(page_name, token)
        page_id = page_data.get("id", "")

        # 게시물 접근 테스트
        if page_id:
            test_posts(page_id, token)
    except requests.HTTPError as e:
        print(f"        [오류] {e.response.status_code}: {e.response.text}")
        raise SystemExit(1)

    # 최종 안내
    print("\n" + "=" * 60)
    print("다음 명령어로 환경변수를 설정하세요 (터미널 재시작 필요):")
    print(f"  setx FB_PAGE_ID \"{page_data.get('id', 'ID를_위에서_확인')}\"")
    print(f"  setx FB_ACCESS_TOKEN \"{token}\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
