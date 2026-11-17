"""판정 에이전트: criteria.yaml 기준으로 공고를 채점해요.

GEMINI_API_KEY가 있으면 Gemini로, 없으면 키워드 규칙(dry-run)으로 판정해요.
"""
from __future__ import annotations

import json
import os
import time

import yaml

PROMPT = """너는 대학생 '민아'의 커리어 코치야. 아래 [민아 정보와 판정 기준]을 보고 [공고]를 판정해.
기사나 공고 내용에 없는 정보는 추측하지 말고 "확인 필요"라고 써.
공고가 아니라 단순 뉴스(수상 소식, 행사 후기 등)이면 is_opportunity를 false로 해.

[민아 정보와 판정 기준]
{criteria}

[공고]
제목: {title}
출처: {source}
내용: {summary}
링크: {url}

아래 JSON 형식으로만 답해:
{{
  "is_opportunity": true/false,
  "type": "해커톤|공모전|데이터경진대회|부트캠프|연합동아리|대외활동|인턴|기타",
  "eligible": "가능|불가|확인 필요",
  "deadline": "YYYY-MM-DD 또는 확인 필요",
  "scores": {{"role_fit": 0-5, "output": 0-5, "tech_depth": 0-5, "fills_gap": 0-5, "schedule_fit": 0-5, "location_fit": 0-5}},
  "one_line": "민아한테 이게 왜 좋은지/별로인지 한 줄",
  "watch_out": "주의할 점 한 줄 (없으면 빈 문자열)"
}}"""


def total_score(scores: dict, criteria: dict) -> int:
    weights = {k: v["weight"] for k, v in criteria["scoring"].items()}
    got = sum(weights[k] * min(max(int(scores.get(k, 0)), 0), 5) for k in weights)
    return round(got / (sum(weights.values()) * 5) * 100)


def _gemini(prompt: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        # 'gemini-flash-latest'는 항상 최신 Flash 모델을 가리키는 별칭이에요.
        # 특정 버전으로 고정하고 싶으면 GitHub 레포 Variables에 GEMINI_MODEL을 넣으세요.
        model=os.getenv("GEMINI_MODEL") or "gemini-flash-latest",
        contents=prompt,
        # 최신 Gemini 모델은 temperature 같은 샘플링 파라미터를 받지 않아서 JSON 출력만 지정해요.
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(resp.text)


KEYWORDS = {
    "role_fit": ["기획", "PM", "서비스", "AX", "데이터", "프로덕트"],
    "output": ["프로젝트", "개발", "출시", "해커톤", "공모전", "MVP"],
    "tech_depth": ["AI", "인공지능", "파이썬", "Python", "데이터", "코딩", "LLM", "에이전트"],
    "fills_gap": ["팀", "협업", "개발자", "데이터 분석", "SQL"],
    "schedule_fit": ["동계", "방학", "단기", "1박", "무박", "주말"],
    "location_fit": ["온라인", "울산", "부산", "비대면"],
}


def _dry_run(item: dict) -> dict:
    """API 키 없이 테스트할 때 쓰는 단순 키워드 채점."""
    text = f"{item['title']} {item['summary']}"
    scores = {k: min(5, sum(w in text for w in ws) * 2) for k, ws in KEYWORDS.items()}
    return {
        "is_opportunity": any(w in text for w in ["모집", "참가자", "접수", "신청"]),
        "type": "기타",
        "eligible": "확인 필요",
        "deadline": "확인 필요",
        "scores": scores,
        "one_line": "(dry-run) 키워드로만 채점한 결과예요. Gemini 키를 넣으면 진짜 판정이 돼요.",
        "watch_out": "",
    }


def judge(items: list[dict], criteria: dict) -> list[dict]:
    use_ai = bool(os.getenv("GEMINI_API_KEY"))
    criteria_text = yaml.safe_dump(criteria, allow_unicode=True, sort_keys=False)
    results = []

    for item in items:
        try:
            if use_ai:
                verdict = _gemini(PROMPT.format(criteria=criteria_text, **item))
                time.sleep(4)  # 무료 한도(분당 요청 수) 보호
            else:
                verdict = _dry_run(item)
        except Exception as e:  # 한 건 실패해도 전체는 계속
            print(f"[judge] 실패: {item['title'][:40]} — {e}")
            continue

        if not verdict.get("is_opportunity"):
            continue
        verdict["score"] = 0 if verdict.get("eligible") == "불가" else total_score(verdict["scores"], criteria)
        results.append({**item, **verdict})

    return results
