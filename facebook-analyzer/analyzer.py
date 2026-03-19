#!/usr/bin/env python3
"""
Facebook Analyzer - Claude API 분석 모듈

세 가지 분석 기능:
  1. analyze_post()     단일 게시물에서 토픽·톤·핵심아이디어·인용구·테마 추출
  2. daily_summary()    하루치 게시물 전체를 마크다운 다이제스트로 요약
  3. update_insights()  전체 히스토리에서 인물의 패턴·가치관·스타일 종합 인사이트 생성
"""

from datetime import datetime
import anthropic
from config import CLAUDE_MODEL


class PostAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call(self, prompt: str, max_tokens: int = 2048) -> str:
        resp = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()

    def analyze_post(self, post: dict) -> dict:
        """
        단일 게시물을 분석하여 구조화된 인사이트를 반환한다.
        반환: {"post_id": str, "analysis_raw": str}
        """
        prompt = f"""다음 Facebook 게시물을 분석하고 구조화된 인사이트를 추출하세요.

게시일: {post.get('created_at', 'N/A')}
링크: {post.get('url', 'N/A')}
게시물 내용:
{post.get('message', '').strip()}

아래 형식으로 정확히 작성하세요 (서론 없이 바로 시작):

**주제**: [핵심 주제 2~5개, 쉼표로 구분]
**톤**: [한 단어: 영감적 / 정보전달 / 개인적 / 성찰적 / 유머러스 / 논쟁적 중 하나]
**핵심 아이디어**:
- [첫 번째 핵심 아이디어, 한 문장]
- [두 번째 핵심 아이디어, 한 문장]
- [세 번째 핵심 아이디어, 해당될 경우]
**인용구**: "[게시물에서 가장 인상적인 문장, 원문 그대로]"
**테마**: [반복되는 상위 테마, 예: 리더십, 회복력, 창의성]
"""
        raw = self._call(prompt, max_tokens=600)
        return {"post_id": post.get("id", ""), "analysis_raw": raw}

    def daily_summary(self, posts: list, date_str: str) -> str:
        """
        하루치 게시물 전체를 마크다운 일간 다이제스트로 요약한다.
        """
        if not posts:
            return f"{date_str}에 게시물이 없습니다."

        post_blocks = []
        for i, p in enumerate(posts, 1):
            block = f"[{i}] ({p.get('created_at', '')[:10]})\n{p.get('message', '').strip()}"
            if p.get("url"):
                block += f"\n링크: {p['url']}"
            post_blocks.append(block)

        posts_text = "\n\n---\n\n".join(post_blocks)

        prompt = f"""당신은 특정 사상가의 Facebook 게시물을 분석하는 전문가입니다.
아래는 {date_str}에 올라온 게시물들입니다.

{posts_text}

다음 구조로 한국어 마크다운 일간 다이제스트를 작성하세요:

## 일간 요약 — {date_str}

**오늘의 게시물 수**: {len(posts)}개

### 오늘의 핵심 테마
[오늘 전체 게시물을 관통하는 2~4가지 테마를 불릿으로]

### 게시물별 한줄 요약
[각 게시물 번호, 한줄 요약, 톤 레이블]

### 오늘의 핵심 게시물
[가장 인상적인 게시물을 선정하고 이유와 함께 인용 또는 요약]

### 반복 패턴
[오늘 여러 번 등장한 단어, 개념, 표현이 있다면 정리]

간결하고 분석적으로 작성하세요. 이 인물의 콘텐츠를 특징짓는 요소에 초점을 맞추세요.
"""
        return self._call(prompt, max_tokens=1500)

    def update_insights(self, all_posts_text: str, existing_insights: str) -> str:
        """
        전체 게시물 히스토리를 바탕으로 마스터 인사이트 문서를 재생성한다.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""당신은 특정 사상가의 소셜미디어 콘텐츠 전체를 분석하는 전문가입니다.

기존 인사이트 (이전 분석 결과, 없을 수 있음):
{existing_insights or "(아직 없음)"}

전체 게시물 요약 (최신순):
{all_posts_text[:15000]}

아래 구조로 마스터 인사이트 마크다운 문서를 업데이트하세요:

# 마스터 인사이트

_최종 업데이트: {today}_

## 콘텐츠 핵심 기둥 (Content Pillars)
[이 인물이 주로 다루는 4~6가지 주요 주제. 각 주제별 빈도 추정치 포함]

## 글쓰기 스타일과 목소리 (Voice)
[어휘 선택, 문장 구조, 직접성, 감정 표현 방식 등 3~5가지 관찰]

## 게시 패턴 (Posting Patterns)
[게시 빈도, 게시물 길이, 질문/목록 사용 여부, 시간대 경향 등]

## 시그니처 표현과 어휘 (Signature Phrases)
[자주 반복해서 사용하는 단어, 표현, 말버릇 정리]

## 핵심 가치관과 신념 (Core Values)
[콘텐츠에서 드러나는 가치관, 지지하는 것, 비판하는 것]

## 독자 관계 전략 (Audience Engagement)
[어떻게 독자와 소통하는가: 스토리텔링, 데이터, 질문, 도발, 영감 등]

## 시간에 따른 변화 (Evolution)
[시간이 지남에 따라 콘텐츠가 어떻게 변화했는지, 관찰 가능한 경우]

## 이 인물을 이해하기 위한 추천 읽기 순서
[처음 접하는 사람이라면 어떤 유형의 게시물부터 읽으면 좋을지]

구체적이고 근거 기반으로 작성하세요. 가능한 경우 실제 게시물 주제나 표현을 인용하세요.
"""
        return self._call(prompt, max_tokens=3000)
