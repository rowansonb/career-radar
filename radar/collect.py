"""공고 수집: RSS 피드 + GitHub Issue 인박스."""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests


def make_id(url: str) -> str:
    return hashlib.sha1(url.strip().encode()).hexdigest()[:12]


def _clean(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def from_rss(sources: dict) -> list[dict]:
    items: list[dict] = []
    limit = sources.get("max_items_per_feed", 15)
    cutoff = datetime.now(timezone.utc) - timedelta(days=sources.get("max_age_days", 14))

    for feed in sources.get("rss", []):
        parsed = feedparser.parse(feed["url"])
        before = len(items)
        for entry in parsed.entries[:limit]:
            published = None
            if entry.get("published"):
                try:
                    published = parsedate_to_datetime(entry.published)
                except (TypeError, ValueError):
                    pass
            if published and published < cutoff:
                continue
            items.append({
                "id": make_id(entry.link),
                "title": entry.get("title", "").strip(),
                "url": entry.link,
                "summary": _clean(entry.get("summary", ""))[:800],
                "source": feed["name"],
                "published": published.isoformat() if published else None,
            })
        print(f"[collect] {feed['name']}: 피드 {len(parsed.entries)}개 → 최근 것 {len(items) - before}개")
    return items


def from_issues() -> list[dict]:
    """'inbox' 라벨이 달린 열린 Issue를 공고로 가져와요. (GitHub Actions 안에서만 동작)"""
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    if not (repo and token):
        return []

    resp = requests.get(
        f"https://api.github.com/repos/{repo}/issues",
        params={"labels": "inbox", "state": "open", "per_page": 50},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    resp.raise_for_status()

    items = []
    for issue in resp.json():
        body = issue.get("body") or ""
        urls = re.findall(r"https?://\S+", body)
        url = urls[0] if urls else issue["html_url"]
        items.append({
            "id": make_id(url),
            "title": issue["title"],
            "url": url,
            "summary": body[:1500],
            "source": "인박스",
            "published": issue["created_at"],
            "issue_number": issue["number"],
        })
    return items
