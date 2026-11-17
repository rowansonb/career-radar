"""실행 진입점: 수집 → 중복 제거 → 판정 → 저장 → 대시보드 → 알림."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from radar.collect import from_issues, from_rss
from radar.judge import judge
from radar.notify import notify
from radar.render import render

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "opportunities.json"
KST = timezone(timedelta(hours=9))


def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", help="RSS 대신 샘플 JSON 파일로 테스트")
    args = ap.parse_args()

    criteria = yaml.safe_load((ROOT / "criteria.yaml").read_text(encoding="utf-8"))
    sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))

    if args.sample:
        collected = load_json(Path(args.sample), [])
    else:
        collected = from_rss(sources) + from_issues()

    history: list[dict] = load_json(DATA, [])
    seen = {x["id"] for x in history}
    fresh = list({x["id"]: x for x in collected if x["id"] not in seen}.values())
    print(f"수집 {len(collected)}개 → 새 공고 {len(fresh)}개 판정 시작")

    run_id = datetime.now(KST).strftime("%Y%m%d-%H%M")
    judged, rejected = judge(fresh, criteria)
    for x in judged:
        x["run_id"] = run_id

    # '공고 아님'으로 판정된 것만 기록 (판정 실패한 건 기록 안 해서 다음 실행 때 재시도)
    skipped = [{"id": i, "skipped": True} for i in rejected]
    failed = len(fresh) - len(judged) - len(rejected)
    if failed:
        print(f"판정 실패 {failed}개 → 다음 실행 때 재시도")
    history = judged + history + skipped
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")

    visible = [x for x in history if not x.get("skipped")]
    render(visible, run_id, ROOT / "docs" / "index.html")

    repo = os.getenv("GITHUB_REPOSITORY", "rowansonb/career-radar")
    owner, name = repo.split("/")
    notify(judged, f"https://{owner}.github.io/{name}/")
    print(f"완료: 추천 {len(judged)}개 (70점↑ {sum(x['score'] >= 70 for x in judged)}개)")


if __name__ == "__main__":
    main()
