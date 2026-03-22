#!/usr/bin/env python3
"""
매일 오전 9시(KST) 뉴스레터 자동 요약 발송 스크립트.
GitHub Actions cron: '0 0 * * *' (UTC 00:00 = KST 09:00)

필요한 GitHub Secrets:
  ANTHROPIC_API_KEY
  GMAIL_ADDRESS       (예: your@gmail.com)
  GMAIL_APP_PASSWORD  (Google 앱 비밀번호 16자리)
  RECIPIENT_EMAIL     (예: sw78.song@samsung.com)
"""

import os
import re
import json
import imaplib
import smtplib
import email as email_lib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from datetime import datetime, timedelta, timezone

import anthropic

# ── 상수 ────────────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def load_config() -> dict:
    """config.json에서 설정 로드 (없으면 기본값)."""
    try:
        with open("config.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


MAX_EMAILS = 20  # fallback (config에서 덮어씀)


# ── Gmail IMAP ───────────────────────────────────────────────────────────────
def connect_imap(address: str, app_password: str) -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(address, app_password)
    return mail


def search_newsletters(mail: imaplib.IMAP4_SSL, max_results: int = 20) -> list:
    """지난 24시간 내 뉴스레터/프로모션 메일 ID 목록 반환."""
    mail.select("inbox")

    # Gmail 전용 검색: Promotions 카테고리 + 최근 1일
    queries = [
        'X-GM-RAW "category:promotions newer_than:1d"',
        'X-GM-RAW "unsubscribe newer_than:1d"',
    ]

    ids: set = set()
    for q in queries:
        try:
            _, data = mail.search("UTF-8", q)
            if data and data[0]:
                ids.update(data[0].split())
        except Exception:
            pass

    # fallback: 일반 SINCE 검색
    if not ids:
        since = (datetime.now(KST) - timedelta(days=1)).strftime("%d-%b-%Y")
        _, data = mail.search(None, f"SINCE {since}")  # 따옴표 없이
        if data and data[0]:
            ids.update(data[0].split())

    return list(ids)[:max_results]


def decode_str(value: str) -> str:
    parts = decode_header(value)
    result = []
    for b, enc in parts:
        if isinstance(b, bytes):
            result.append(b.decode(enc or "utf-8", errors="ignore"))
        else:
            result.append(b)
    return "".join(result)


def decode_body(part) -> str:
    # decode=True가 base64/QP 전송 인코딩을 자동 처리
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="ignore")
    except Exception:
        return payload.decode("utf-8", errors="ignore")


def extract_text(msg) -> str:
    """이메일에서 텍스트 추출 (plain → html 우선순위)."""
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                continue
            if ct == "text/plain" and not text:
                text = decode_body(part)
            elif ct == "text/html" and not text:
                # HTML에서 태그 제거
                raw = decode_body(part)
                raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
                raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
                raw = re.sub(r"<[^>]+>", " ", raw)
                raw = re.sub(r"\s+", " ", raw)
                text = raw.strip()
    else:
        text = decode_body(msg)
    return text[:3000]


def fetch_emails(mail: imaplib.IMAP4_SSL, ids: list[str]) -> list[dict]:
    result = []
    for uid in ids:
        try:
            _, data = mail.fetch(uid, "(RFC822)")
            raw = data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject = decode_str(msg.get("Subject", "(제목 없음)"))
            sender = decode_str(msg.get("From", ""))
            body = extract_text(msg)

            # 원문 링크 추출 (List-Post, X-Original-URL 등)
            link = msg.get("List-Archive", "") or msg.get("X-Original-URL", "")

            result.append({
                "subject": subject,
                "sender": sender,
                "body": body,
                "link": link,
            })
        except Exception as e:
            print(f"  WARN: fetch error for uid {uid}: {e}")
    return result


# ── Claude API ───────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """아래 {count}개의 뉴스레터/구독 이메일을 분석해서 한국어 HTML 요약 리포트를 만들어주세요.

오늘: {today}

[이메일 목록]
{emails}

[규칙]
- 중요도 순으로 넘버링 (1번이 가장 중요)
- 각 항목마다 bullet 최대 3개, bullet 1개 = 2줄 이하, 매우 간결하게
- 핵심 키워드는 <strong> 태그 강조
- 원문 링크: body에서 http URL 추출, 없으면 발신자 도메인 사용
- 모든 텍스트는 2줄 이하

[HTML 구조 - 이 형식 그대로 사용]
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:28px 16px;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#111827;">
<div style="max-width:640px;margin:0 auto;">

  <!-- 헤더 -->
  <div style="background:#18181b;color:#fff;padding:24px 28px;border-radius:14px 14px 0 0;margin-bottom:2px;">
    <div style="font-size:20px;font-weight:800;letter-spacing:-0.3px;">📋 뉴스레터 요약</div>
    <div style="font-size:12px;color:#a1a1aa;margin-top:6px;">{today} &nbsp;·&nbsp; {count}건 분석</div>
  </div>

  <!-- 카드들 (아래 구조 반복) -->
  <div style="background:#ffffff;border-left:4px solid #6366f1;padding:20px 24px;margin-bottom:2px;">
    <div style="font-size:16px;font-weight:900;color:#0f172a;line-height:1.45;margin-bottom:10px;">
      <span style="color:#6366f1;font-weight:900;margin-right:6px;">N.</span>제목
      &nbsp;<a href="원문URL" style="font-size:12px;font-weight:400;color:#6366f1;text-decoration:none;">[원문 →]</a>
    </div>
    <ul style="margin:0;padding-left:18px;">
      <li style="font-size:13px;color:#374151;line-height:1.75;margin-bottom:3px;">bullet 1</li>
      <li style="font-size:13px;color:#374151;line-height:1.75;margin-bottom:3px;">bullet 2</li>
      <li style="font-size:13px;color:#374151;line-height:1.75;">bullet 3</li>
    </ul>
  </div>

  <!-- 마지막 카드는 border-radius:0 0 14px 14px 추가 -->

  <!-- 푸터 -->
  <div style="text-align:center;font-size:11px;color:#9ca3af;padding:20px 0 4px;">
    🤖 Claude 자동 생성 · 매일 오전 9시 KST
  </div>

</div>
</body>
</html>

완성된 HTML 코드만 반환하세요. 설명 없이."""


def generate_html(emails: list[dict], today: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    email_text = ""
    for i, e in enumerate(emails, 1):
        email_text += f"--- [{i}] ---\n제목: {e['subject']}\n발신: {e['sender']}\n본문: {e['body'][:2000]}\n\n"

    prompt = PROMPT_TEMPLATE.format(
        count=len(emails),
        today=today,
        emails=email_text,
    )

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Gmail SMTP 발송 ──────────────────────────────────────────────────────────
def send_email(address: str, app_password: str, recipient: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    recipients = [recipient] if isinstance(recipient, str) else recipient
    msg["Subject"] = subject
    msg["From"] = address
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
        s.login(address, app_password)
        s.sendmail(address, recipients, msg.as_string())


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    cfg = load_config()

    # enabled 체크 — False면 조용히 종료
    if cfg.get("enabled") is False:
        print("서비스 비활성화 상태 (config.enabled=false). 건너뜀.")
        return

    address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    # 수신자 목록: config.recipient_emails(배열) 우선, 없으면 recipient_email(단수) or secret
    recipients = (
        cfg.get("recipient_emails")
        or ([cfg["recipient_email"]] if cfg.get("recipient_email") else None)
        or [os.environ.get("RECIPIENT_EMAIL", address)]
    )
    max_emails = int(cfg.get("max_emails", MAX_EMAILS))

    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y년 %m월 %d일")
    subject = f"📋 뉴스레터 요약 | {now_kst.strftime('%Y.%m.%d')}"

    print(f"[{now_kst.strftime('%Y-%m-%d %H:%M KST')}] 시작 | 수신: {recipients} | 최대: {max_emails}건")

    # 1. Gmail 연결 및 메일 검색
    print("Gmail 연결 중...")
    mail = connect_imap(address, app_password)
    ids = search_newsletters(mail, max_results=max_emails)
    print(f"메일 {len(ids)}건 발견")

    if not ids:
        html = f"""<body style="font-family:Arial;padding:40px;color:#555;text-align:center;">
        <h2>📋 뉴스레터 요약 | {today}</h2>
        <p style="color:#999;">오늘 수신된 뉴스레터가 없습니다.</p>
        </body>"""
        send_email(address, app_password, recipients, subject, html)
        print("빈 리포트 발송 완료")
        return

    # 2. 메일 본문 읽기
    print("메일 내용 읽는 중...")
    emails = fetch_emails(mail, ids)
    mail.logout()
    print(f"{len(emails)}건 처리 완료")

    # 3. Claude로 HTML 생성
    print("Claude로 요약 생성 중...")
    html = generate_html(emails, today)

    # HTML 태그 감지 안 되면 기본 래핑
    if "<!DOCTYPE" not in html and "<html" not in html:
        html = f"<html><body>{html}</body></html>"

    # 4. 이메일 발송
    print(f"발송 중 → {recipients}")
    send_email(address, app_password, recipients, subject, html)
    print("완료!")


if __name__ == "__main__":
    main()
