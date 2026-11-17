# 🛰️ career-radar — 민아 전용 커리어 레이더

해커톤·공모전·부트캠프·대외활동 공고를 모아서, **내 상황에 맞는지 AI 에이전트가 판정**하고
매주 월·목 아침에 대시보드와 디스코드로 알려주는 개인 자동화 프로젝트.

**대시보드:** https://rowansonb.github.io/career-radar/

## 어떻게 동작하나

```
[매주 월·목 07:07, GitHub Actions]
   │
   ├─ 수집   Google 뉴스 RSS + GitHub Issue 인박스          radar/collect.py
   ├─ 중복제거  이미 본 공고는 건너뜀 (data/opportunities.json)
   ├─ 판정   Gemini가 criteria.yaml 기준으로 6개 항목 채점     radar/judge.py
   ├─ 대시보드  docs/index.html 생성 → GitHub Pages 배포       radar/render.py
   └─ 알림   새 공고 TOP 3를 디스코드로 전송                  radar/notify.py
```

- **판정 기준은 `criteria.yaml`에만 있어요.** 상황이 바뀌면(시간, 희망 직무 등) 이 파일만 고치면 돼요.
- **수집처는 `sources.yaml`에서** 추가/삭제해요.

## 인박스 쓰는 법 (폰에서도 가능)

1. 레포의 **Issues → New issue**
2. 제목에 공고 이름, 본문에 공고 링크 + 공고 내용 복붙
3. 오른쪽 **Labels**에서 `inbox` 선택 → 1~2분 뒤 자동으로 판정돼서 대시보드에 올라감

## 처음 세팅 (1회만)

1. **Gemini API 키 발급**: https://aistudio.google.com/apikey → Create API key
2. **레포 Secrets 등록**: Settings → Secrets and variables → Actions → New repository secret
   - `GEMINI_API_KEY` = 발급받은 키
   - `DISCORD_WEBHOOK_URL` = 디스코드 채널 설정 → 연동 → 웹후크 → 새 웹후크 → URL 복사 (선택)
3. **GitHub Pages 켜기**: Settings → Pages → Source: `Deploy from a branch` → Branch: `main`, 폴더 `/docs` → Save
4. **`inbox` 라벨 만들기**: Issues → Labels → New label → 이름 `inbox`
5. **첫 실행**: Actions 탭 → career-radar → Run workflow
6. 브라우저 시작페이지를 대시보드 주소로 설정

## 로컬 테스트

```bash
pip install -r requirements.txt
python -m radar.main --sample samples/sample.json   # API 키 없으면 키워드 규칙으로 dry-run
```

## 다음 단계 아이디어

- [ ] 판정 정확도 평가셋 만들기 (공고 30개에 직접 정답 달고, 프롬프트 버전별 정확도 비교)
- [ ] 약관·robots.txt 확인 후 공고 사이트 직접 수집 추가
- [ ] "지원함/보류/패스" 상태 관리 (Notion 연동)
- [ ] 마감 D-3 리마인더
