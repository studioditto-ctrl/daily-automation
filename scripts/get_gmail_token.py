#!/usr/bin/env python3
"""
Gmail OAuth2 refresh_token 획득 스크립트 (로컬 1회 실행용)

실행 전 준비:
  1. Google Cloud Console → Gmail API 활성화
  2. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱 유형)
  3. 아래 환경 변수 설정:
       Windows:  set GMAIL_CLIENT_ID=xxx  &&  set GMAIL_CLIENT_SECRET=yyy
       Mac/Linux: export GMAIL_CLIENT_ID=xxx && export GMAIL_CLIENT_SECRET=yyy

실행:
  pip install google-auth-oauthlib
  python scripts/get_gmail_token.py

결과로 출력되는 refresh_token을 GitHub Secrets에 GMAIL_REFRESH_TOKEN으로 등록하세요.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
    client_id     = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("[ERROR] 환경 변수를 먼저 설정하세요.")
        print()
        print("  Windows:")
        print("    set GMAIL_CLIENT_ID=your_client_id")
        print("    set GMAIL_CLIENT_SECRET=your_client_secret")
        print()
        print("  Mac/Linux:")
        print("    export GMAIL_CLIENT_ID=your_client_id")
        print("    export GMAIL_CLIENT_SECRET=your_client_secret")
        return

    config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(config, SCOPES)
    creds = flow.run_local_server(port=0)

    print()
    print("=" * 60)
    print("✅ 인증 성공! 아래 값을 GitHub Secrets에 등록하세요.")
    print("=" * 60)
    print()
    print(f"GMAIL_CLIENT_ID     = {creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET = {creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print()

    # 백업용 로컬 저장 (절대 Git에 커밋 금지)
    with open("token_debug.json", "w") as f:
        json.dump({
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "refresh_token": creds.refresh_token,
        }, f, indent=2)
    print("📁 token_debug.json 에도 저장됨 — Git에 커밋하지 마세요!")


if __name__ == "__main__":
    main()
