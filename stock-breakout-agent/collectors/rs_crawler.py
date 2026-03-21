"""
RS(상대강도) 데이터 수집기 — StockEasy (intellio.kr)

로그인 방식: Google OAuth (이메일 + 비밀번호)
데이터: https://stockeasy.intellio.kr/rs-rank?tab=integrated_rs
렌더링: Next.js SPA (JavaScript 실행 후 테이블 로드)

.env 필수 항목:
  GOOGLE_EMAIL=studioditto@gmail.com
  GOOGLE_PASSWORD=...
"""
import asyncio
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from playwright.async_api import async_playwright, Page, Browser
import config
import collectors.site_config as sc


# ────────────────────────────────────────
# Google OAuth 로그인
# ────────────────────────────────────────
async def _google_oauth(page: Page) -> bool:
    """
    Google OAuth 로그인 수행
    - 이메일 입력 → 다음 → 비밀번호 입력 → 다음
    - StockEasy로 리디렉션 완료 시 True 반환
    """
    print("[RS Crawler] Google OAuth 로그인 시작")

    # 1) 이메일 입력
    await page.wait_for_selector(sc.GOOGLE_EMAIL_INPUT, timeout=sc.ACTION_TIMEOUT)
    await page.fill(sc.GOOGLE_EMAIL_INPUT, config.GOOGLE_EMAIL)
    await page.keyboard.press("Enter")
    print(f"[RS Crawler] 이메일 입력: {config.GOOGLE_EMAIL}")

    # 2) 비밀번호 페이지 대기 및 입력
    await page.wait_for_selector(sc.GOOGLE_PASSWORD_INPUT, timeout=sc.ACTION_TIMEOUT)
    await asyncio.sleep(0.5)  # 필드 활성화 대기
    await page.fill(sc.GOOGLE_PASSWORD_INPUT, config.GOOGLE_PASSWORD)
    await page.keyboard.press("Enter")
    print("[RS Crawler] 비밀번호 입력 완료")

    # 3) StockEasy 리디렉션 대기
    try:
        await page.wait_for_url(
            f"**{sc.LOGIN_SUCCESS_URL_PATTERN}**",
            timeout=sc.PAGE_LOAD_TIMEOUT,
        )
        print(f"[RS Crawler] 로그인 성공: {page.url}")
        return True
    except Exception:
        print(f"[RS Crawler] 로그인 실패 — 현재 URL: {page.url}")
        return False


async def login(page: Page) -> bool:
    """
    intellio.kr 로그인 페이지 → Google OAuth 처리

    Returns:
        True: 로그인 및 StockEasy 리디렉션 성공
        False: 실패
    """
    try:
        await page.goto(sc.LOGIN_URL, timeout=sc.PAGE_LOAD_TIMEOUT)
        await page.wait_for_load_state("networkidle")

        # Google 로그인 버튼 클릭
        google_btn = await page.wait_for_selector(
            sc.GOOGLE_LOGIN_BTN, timeout=sc.ACTION_TIMEOUT
        )
        await google_btn.click()
        print("[RS Crawler] Google 로그인 버튼 클릭")

        # Google 로그인 팝업 또는 리디렉션 처리
        # Google은 때로 새 팝업을 열지 않고 현재 페이지에서 진행
        await page.wait_for_load_state("networkidle")

        return await _google_oauth(page)

    except Exception as e:
        print(f"[RS Crawler] 로그인 오류: {e}")
        return False


# ────────────────────────────────────────
# 테이블 헤더 자동 감지
# ────────────────────────────────────────
async def _detect_column_indices(page: Page) -> dict[str, int]:
    """
    테이블 헤더 텍스트를 읽어 필드명 → 열 인덱스 매핑 반환
    AUTO_DETECT_COLUMNS=True 일 때 사용
    """
    header_cells = await page.query_selector_all("thead th, thead td, [role='columnheader']")
    mapping: dict[str, int] = {}

    for i, cell in enumerate(header_cells):
        text = (await cell.inner_text()).strip()
        for header_key, field_name in sc.COLUMN_HEADER_MAP.items():
            if header_key in text:
                mapping[field_name] = i
                break

    print(f"[RS Crawler] 컬럼 자동 감지: {mapping}")
    return mapping


# ────────────────────────────────────────
# 숫자 파싱
# ────────────────────────────────────────
def _parse_number(text: str) -> float:
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _is_stock_code(text: str) -> bool:
    """6자리 숫자 종목코드 여부"""
    return bool(re.match(r"^\d{6}$", text.strip()))


# ────────────────────────────────────────
# 테이블 데이터 파싱
# ────────────────────────────────────────
async def _parse_table_page(page: Page, col_map: dict[str, int]) -> list[dict]:
    """현재 페이지의 RS 랭킹 테이블 파싱"""
    rows = await page.query_selector_all(sc.RS_ROW_SELECTOR)
    candidates = []

    code_idx   = col_map.get("code", 0)
    name_idx   = col_map.get("name", 1)
    rs_idx     = col_map.get("rs_score", 2)
    sector_idx = col_map.get("sector", -1)

    for row in rows:
        cells = await row.query_selector_all("td, [role='cell']")
        if not cells:
            continue
        try:
            texts = [await c.inner_text() for c in cells]
            if len(texts) <= max(code_idx, name_idx, rs_idx):
                continue

            code     = texts[code_idx].strip()
            name     = texts[name_idx].strip()
            rs_raw   = texts[rs_idx].strip() if rs_idx < len(texts) else ""
            rs_score = _parse_number(rs_raw)
            sector   = texts[sector_idx].strip() if 0 <= sector_idx < len(texts) else ""

            # 종목코드가 숫자가 아닌 경우, 셀 전체를 스캔해서 코드 찾기
            if not _is_stock_code(code):
                for t in texts:
                    if _is_stock_code(t):
                        code = t.strip()
                        break
                else:
                    continue  # 코드를 찾지 못하면 스킵

            if rs_score <= 0:
                continue

            candidates.append({
                "code":     code,
                "name":     name,
                "rs_score": rs_score,
                "sector":   sector,
            })

        except Exception:
            continue

    return candidates


# ────────────────────────────────────────
# 전체 수집 플로우
# ────────────────────────────────────────
async def fetch_rs_ranking(page: Page) -> list[dict]:
    """
    RS 랭킹 페이지 이동 후 전체 데이터 수집

    Returns:
        [{code, name, rs_score, sector}, ...]  RS점수 내림차순
    """
    print(f"[RS Crawler] RS 랭킹 페이지 이동: {sc.RS_RANK_URL}")
    await page.goto(sc.RS_RANK_URL, timeout=sc.PAGE_LOAD_TIMEOUT)

    # Next.js SPA 데이터 로드 대기
    await page.wait_for_load_state("networkidle")
    await page.wait_for_selector(sc.RS_TABLE_WAIT_SELECTOR, timeout=sc.TABLE_WAIT_TIMEOUT)
    await asyncio.sleep(1.5)  # 추가 렌더링 대기

    # 컬럼 자동 감지
    col_map: dict[str, int] = {}
    if sc.AUTO_DETECT_COLUMNS:
        col_map = await _detect_column_indices(page)

    # 열 감지 실패 시 기본값
    if not col_map:
        col_map = {"code": 0, "name": 1, "rs_score": 2, "sector": 3}
        print(f"[RS Crawler] 컬럼 감지 실패, 기본값 사용: {col_map}")

    all_candidates: list[dict] = []
    page_num = 1

    while True:
        print(f"[RS Crawler] {page_num}페이지 파싱 중...")
        rows = await _parse_table_page(page, col_map)
        all_candidates.extend(rows)
        print(f"[RS Crawler] 이번 페이지: {len(rows)}개 수집")

        if not sc.PAGINATION_ENABLED or page_num >= sc.MAX_PAGES:
            break

        next_btn = await page.query_selector(sc.NEXT_PAGE_SELECTOR)
        if not next_btn:
            break

        is_disabled = await next_btn.get_attribute("disabled")
        if is_disabled is not None:
            break

        await next_btn.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        page_num += 1

    all_candidates.sort(key=lambda x: x["rs_score"], reverse=True)
    print(f"[RS Crawler] 총 {len(all_candidates)}개 종목 수집 완료")
    return all_candidates


async def run_collection() -> list[dict]:
    """
    전체 수집 플로우 실행 (브라우저 시작 → 로그인 → 수집 → 종료)

    Returns:
        RS 랭킹 종목 리스트. 실패 시 빈 리스트.
    """
    if not config.GOOGLE_EMAIL or not config.GOOGLE_PASSWORD:
        print("[RS Crawler] GOOGLE_EMAIL / GOOGLE_PASSWORD가 .env에 설정되지 않았습니다.")
        return []

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        try:
            logged_in = await login(page)
            if not logged_in:
                print("[RS Crawler] 로그인 실패로 수집 중단")
                return []

            candidates = await fetch_rs_ranking(page)
            return candidates

        except Exception as e:
            print(f"[RS Crawler] 수집 중 오류: {e}")
            return []
        finally:
            await browser.close()


# 직접 실행 시 테스트
if __name__ == "__main__":
    results = asyncio.run(run_collection())
    print(f"\n수집 결과: {len(results)}개")
    for r in results[:10]:
        print(r)
