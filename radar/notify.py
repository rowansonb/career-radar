"""디스코드 알림 (DISCORD_WEBHOOK_URL이 없으면 건너뜀)."""
from __future__ import annotations

import os

import requests


def notify(new_items: list[dict], dashboard_url: str) -> None:
    hook = os.getenv("DISCORD_WEBHOOK_URL")
    if not hook or not new_items:
        return

    top = sorted(new_items, key=lambda x: x["score"], reverse=True)[:3]
    lines = [f"**[{x['score']}점] {x['title']}**\n{x['one_line']}\n<{x['url']}>" for x in top]
    content = f"🛰️ 새 공고 {len(new_items)}개 — 추천 TOP {len(top)}\n\n" + "\n\n".join(lines)
    content += f"\n\n전체 보기 → {dashboard_url}"

    requests.post(hook, json={"content": content[:1990]}, timeout=20).raise_for_status()
