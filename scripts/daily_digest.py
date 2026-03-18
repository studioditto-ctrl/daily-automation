#!/usr/bin/env python3
"""
매일 오전 9시(KST) 뉴스레터 자동 요약 발송 스크립트.
GitHub Actions cron: '0 0 * * *' (UTC 00:00 = KST 09:00)

필요한 GitHub Secrets:
  ANTHROPIC_API_KEY
  GMAIL_CLIENT_ID
  GMAIL_CLIENT_SECRET
  GMAIL_REFRESH_TOKEN
"""

import os
import base64
import re
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── 상수 ──────────────────────────────────────────────────
RECIPIENT = "sw78.song@samsung.com"
KST = timezone(timedelta(hours=9))
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


# ── Gmail 인증 ─────────────────────────────────────────────
def build_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


# ── 메일 수집 ──────────────────────────────────────────────
def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def decode_body(payload: dict) -> str:
    """payload에서 텍스트 본문 추출 (재귀)."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data", "")

    if mime == "text/plain" and data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    if mime == "text/html" and data:
        html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", text).strip()

    for part in payload.get("parts", []):
        result = decode_body(part)
        if result:
            return result
    return ""


def is_newsletter(sender: str, subject: str) -> bool:
    keywords = [
        "newsletter", "noreply", "no-reply", "substack", "digest",
        "weekly", "daily", "briefing", "roundup", "mailchimp",
        "뉴스레터", "브리핑", "주간", "일간",
    ]
    text = (sender + subject).lower()
    return any(k in text for k in keywords)


def fetch_emails(service) -> list[dict]:
    print("[STEP 2] 뉴스레터 검색 중 (newer_than:1d)...")
    res = service.users().messages().list(
        userId="me", q="newer_than:1d", maxResults=50
    ).execute()

    messages = res.get("messages", [])
    print(f"        검색 결과: {len(messages)}건")

    results = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        headers = detail.get("payload", {}).get("headers", [])
        subject = get_header(headers, "Subject")
        sender  = get_header(headers, "From")
        date    = get_header(headers, "Date")

        if not is_newsletter(sender, subject):
            continue

        body = decode_body(detail.get("payload", {}))[:3000]
        results.append({"subject": subject, "sender": sender, "date": date, "body": body})
        print(f"        수집: {subject[:70]}")

    print(f"        필터 후: {len(results)}건")
    return results


# ── Claude HTML 생성 ───────────────────────────────────────
def generate_html(emails: list[dict], today_kst: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    if not emails:
        email_text = "(오늘 수신된 뉴스레터가 없습니다.)"
    else:
        blocks = []
        for i, e in enumerate(emails, 1):
            blocks.append(
                f"[{i}] 제목: {e['subject']}\n"
                f"    발신: {e['sender']}\n"
                f"    날짜: {e['date']}\n"
                f"    본문: {e['body']}\n"
            )
        email_text = "\n---\n".join(blocks)

    prompt = f"""아래 뉴스레터들을 중요도 순으로 정렬해 HTML 이메일을 생성하세요.

오늘: {today_kst} | 수신자: {RECIPIENT}

=== 뉴스레터 ===
{email_text}

=== 출력 형식 ===
순수 HTML div만 반환하세요 (<!DOCTYPE>, <html>, <head>, <body> 제외).
아래 구조를 정확히 따르세요:

<div style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;background:#f0f2f5;padding:28px 16px;">
<div style="max-width:620px;margin:0 auto;">

  <!-- 헤더 -->
  <div style="background:#18181b;color:#fff;padding:24px 28px;border-radius:14px 14px 0 0;margin-bottom:2px;">
    <div style="font-size:18px;font-weight:700;">📋 뉴스레터 요약</div>
    <div style="font-size:12px;color:#71717a;margin-top:5px;">{today_kst} · N건</div>
  </div>

  <!-- 각 메일 카드 (번호순, 마지막 카드만 border-radius:0 0 14px 14px) -->
  <div style="background:#fff;border-left:5px solid #e5e7eb;padding:20px 22px;margin-bottom:3px;">
    <div style="font-size:17px;font-weight:900;color:#0f172a;line-height:1.4;margin-bottom:12px;">
      N. 메일 제목
      <span style="font-weight:400;font-size:13px;margin-left:6px;">(<a href="원문URL" style="color:#6366f1;text-decoration:none;">원문 링크</a>)</span>
    </div>
    <ul style="padding-left:18px;margin:0;">
      <li style="font-size:13px;color:#4b5563;line-height:1.7;margin-bottom:4px;">요약 1 — <strong>핵심키워드</strong>.</li>
      <li style="font-size:13px;color:#4b5563;line-height:1.7;margin-bottom:4px;">요약 2.</li>
      <li style="font-size:13px;color:#4b5563;line-height:1.7;">요약 3.</li>
    </ul>
  </div>

  <!-- 푸터 -->
  <div style="text-align:center;font-size:11px;color:#9ca3af;padding:18px 0 4px;">
    🤖 Claude 자동 생성 · 매일 오전 9시 · {RECIPIENT}
  </div>

</div>
</div>

=== 규칙 ===
- 제목은 원문 그대로 (번역 금지)
- bullet 최대 3개, 각 2줄 이내, 핵심 키워드 <strong> 강조
- 원문 링크는 메일 본문의 웹뷰 URL 사용, 없으면 "#" 사용
- HTML 코드블록(```) 없이 순수 HTML만 반환
"""

    print("[STEP 3] Claude API 호출 중...")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    html = resp.content[0].text.strip()

    # 혹시 코드블록이 포함됐을 경우 제거
    html = re.sub(r"^```[a-zA-Z]*\n?", "", html)
    html = re.sub(r"\n?```$", "", html)
    print(f"        HTML 생성 완료 ({len(html):,}자)")
    return html


# ── 이메일 발송 ────────────────────────────────────────────
def send_email(service, html_body: str, today_kst: str):
    profile = service.users().getProfile(userId="me").execute()
    sender  = profile.get("emailAddress", "me")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📋 뉴스레터 요약 | {today_kst}"
    msg["From"]    = sender
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText("HTML 이메일 클라이언트에서 확인하세요.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"[STEP 4] 발송 완료 → {RECIPIENT} (Message ID: {sent.get('id')})")


# ── 메인 ──────────────────────────────────────────────────
def main():
    # 환경 변수 체크
    missing = [e for e in ["ANTHROPIC_API_KEY", "GMAIL_CLIENT_ID",
                            "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"]
               if not os.environ.get(e)]
    if missing:
        print(f"[ERROR] 누락된 환경 변수: {', '.join(missing)}")
        sys.exit(1)

    now = datetime.now(KST)
    today_kst = now.strftime("%Y년 %m월 %d일")
    print(f"[START] {today_kst} 뉴스레터 다이제스트 시작")

    print("[STEP 1] Gmail 인증...")
    service = build_service()
    print("        인증 완료")

    emails  = fetch_emails(service)
    html    = generate_html(emails, today_kst)
    send_email(service, html, today_kst)

    print("[DONE] 완료")


if __name__ == "__main__":
    main()
