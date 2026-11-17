"""docs/index.html 대시보드 생성 → GitHub Pages로 배포돼요."""
from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>민아 커리어 레이더</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --line:#262a33; --text:#e8eaed; --sub:#9aa0aa; --accent:#7cf2c1; --warn:#ffb86b; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:Pretendard,system-ui,sans-serif; }}
  main {{ max-width:880px; margin:0 auto; padding:40px 20px 80px; }}
  header {{ display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; margin-bottom:28px; }}
  h1 {{ margin:0; font-size:26px; letter-spacing:-0.02em; }}
  h1 span {{ color:var(--accent); }}
  .meta {{ color:var(--sub); font-size:13px; }}
  .tabs {{ display:flex; gap:8px; margin-bottom:20px; }}
  .tabs button {{ background:none; border:1px solid var(--line); color:var(--sub); padding:7px 14px; border-radius:999px; cursor:pointer; font:inherit; font-size:14px; }}
  .tabs button.on {{ border-color:var(--accent); color:var(--accent); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px 20px; margin-bottom:12px; display:grid; grid-template-columns:64px 1fr; gap:16px; }}
  .score {{ font-size:28px; font-weight:700; text-align:center; line-height:1; padding-top:4px; }}
  .score small {{ display:block; font-size:11px; font-weight:400; color:var(--sub); margin-top:6px; }}
  .hi {{ color:var(--accent); }} .mid {{ color:var(--text); }} .lo {{ color:var(--sub); }}
  .title {{ font-size:16px; font-weight:600; color:var(--text); text-decoration:none; }}
  .title:hover {{ text-decoration:underline; }}
  .tags {{ display:flex; gap:6px; flex-wrap:wrap; margin:8px 0; }}
  .tag {{ font-size:12px; padding:3px 8px; border-radius:6px; background:#22262f; color:var(--sub); }}
  .tag.new {{ background:rgba(124,242,193,.12); color:var(--accent); }}
  .tag.no {{ background:rgba(255,107,107,.12); color:#ff8a8a; }}
  .why {{ font-size:14px; line-height:1.55; margin:0; }}
  .warn {{ font-size:13px; color:var(--warn); margin:6px 0 0; }}
  .empty {{ color:var(--sub); text-align:center; padding:60px 0; }}
</style>
</head>
<body>
<main>
  <header>
    <h1>민아 커리어 <span>레이더</span></h1>
    <div class="meta">마지막 업데이트 {updated} · 새 공고 {new_count}개</div>
  </header>
  <div class="tabs">
    <button class="on" data-f="new">이번 회차 신규</button>
    <button data-f="top">추천 (70점↑)</button>
    <button data-f="all">전체</button>
  </div>
  <div id="list"></div>
</main>
<script>
const DATA = {data};
const RUN = "{run_id}";
function cls(s) {{ return s >= 70 ? "hi" : s >= 45 ? "mid" : "lo"; }}
function esc(s) {{ const d = document.createElement("div"); d.textContent = s ?? ""; return d.innerHTML; }}
function draw(f) {{
  const rows = DATA.filter(x => f === "all" || (f === "new" ? x.run_id === RUN : x.score >= 70));
  document.getElementById("list").innerHTML = rows.length ? rows.map(x => `
    <article class="card">
      <div class="score ${{cls(x.score)}}">${{x.score}}<small>/ 100</small></div>
      <div>
        <a class="title" href="${{esc(x.url)}}" target="_blank" rel="noopener">${{esc(x.title)}}</a>
        <div class="tags">
          ${{x.run_id === RUN ? '<span class="tag new">NEW</span>' : ''}}
          <span class="tag">${{esc(x.type)}}</span>
          <span class="tag ${{x.eligible === '불가' ? 'no' : ''}}">지원 ${{esc(x.eligible)}}</span>
          <span class="tag">마감 ${{esc(x.deadline)}}</span>
          <span class="tag">${{esc(x.source)}}</span>
        </div>
        <p class="why">${{esc(x.one_line)}}</p>
        ${{x.watch_out ? `<p class="warn">⚠ ${{esc(x.watch_out)}}</p>` : ''}}
      </div>
    </article>`).join("") : '<p class="empty">해당하는 공고가 없어요</p>';
}}
document.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {{
  document.querySelectorAll(".tabs button").forEach(o => o.classList.remove("on"));
  b.classList.add("on"); draw(b.dataset.f);
}});
draw(DATA.some(x => x.run_id === RUN) ? "new" : "top");
if (!DATA.some(x => x.run_id === RUN)) {{
  document.querySelectorAll(".tabs button").forEach(o => o.classList.toggle("on", o.dataset.f === "top"));
}}
</script>
</body>
</html>
"""


def _not_expired(item: dict) -> bool:
    d = item.get("deadline", "")
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() >= datetime.now(KST).date()
    except ValueError:
        return True  # '확인 필요'는 남겨둠


def render(all_items: list[dict], run_id: str, out: Path) -> None:
    rows = sorted(filter(_not_expired, all_items), key=lambda x: (x["run_id"] == run_id, x["score"]), reverse=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.format(
        data=json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"),
        run_id=html.escape(run_id),
        updated=datetime.now(KST).strftime("%m/%d %H:%M"),
        new_count=sum(x["run_id"] == run_id for x in rows),
    ), encoding="utf-8")
