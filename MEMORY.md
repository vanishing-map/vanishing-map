# 만들기 기록 - vanishing_map

> 이 파일은 이 MVP를 어떤 과정으로 만들었는지 남기는 기록입니다.
> 나중에 복기하거나 사회혁신 AI 에이전트 워크플로 사례로 정리할 때 씁니다.

## 한눈에 보기
- 무엇을: 한국의 귀농·귀촌 및 관계인구 정책에서 전국 단위 출발지→도착지 이동 흐름을 한눈에 볼 수 있는 통합 시각화가 부족해, 각 지자체가 자체 데이터만으로 유입·유출을 해석하고 과잉 경쟁하는 문제가 있다.
- 누구를 위해: 전국 이동 흐름을 바탕으로 지역 정책과 홍보 방향을 판단해야 하는 청도군 실무자
- 핵심 흐름: 공공 통계 샘플 입력 -> flow 데이터 표준화 -> 전국 flow map 표시 -> 실무자 해석 검토
- 스택/도구: Codex, 정적 HTML/CSS/JavaScript, 공공데이터/KOSIS 샘플 CSV
- 시작: 2026-06-27

---

## 기록

### 2026-06-27 문제 정의
- **정한 것 / 한 것**: 필수 산출물 구조와 3시간 MVP 범위를 정리했다.
- **왜**: 팀별 결과물을 같은 구조로 남겨 이후 사례집과 워크플로 라이브러리로 재사용하기 위해서다.
- **어떻게**: 반응형 질문 답변을 표준 필드로 정규화해 PLAN.md, workshop.json, WORKFLOW_ANALYSIS.md, CASE_STUDY.md, MEMORY.md에 기록했다.
- **막힌 점 / 바꾼 점**: 없음
- **배운 것 / 다음**: 사용자가 PLAN.md 기준으로 MVP를 구현하고, 완료 후 검수 포인트와 기록을 보완한다.

### 2026-06-27 시각화 확장 설계 반영
- **정한 것 / 한 것**: 필수 산출물 구조와 3시간 MVP 범위를 정리했다.
- **왜**: 팀별 결과물을 같은 구조로 남겨 이후 사례집과 워크플로 라이브러리로 재사용하기 위해서다.
- **어떻게**: 반응형 질문 답변을 표준 필드로 정규화해 PLAN.md, workshop.json, WORKFLOW_ANALYSIS.md, CASE_STUDY.md, MEMORY.md에 기록했다.
- **막힌 점 / 바꾼 점**: 없음
- **배운 것 / 다음**: 사용자가 PLAN.md 기준으로 MVP를 구현하고, 완료 후 검수 포인트와 기록을 보완한다.

### 2026-06-27 데이터 수집 1차
- **정한 것 / 한 것**: 사용자 제공 KOSIS `DT_1B26001_A01` API를 호출해 원본 JSON을 저장하고, 최근 6개월 시도 단위 이동자수 CSV로 정규화했다.
- **왜**: 구현 전 실제 데이터 구조를 확인해 flow map에 바로 쓸 수 있는 데이터인지 판단하기 위해서다.
- **어떻게**: 원본은 `data/kosis-dt-1b26001-a01-raw.json`, 전체 월별 정규화본은 `data/kosis-dt-1b26001-a01-monthly-sido.csv`, 최신월 스냅샷은 `data/kosis-dt-1b26001-a01-latest-sido-snapshot.csv`, 메타데이터는 `data/kosis-dt-1b26001-a01-metadata.json`에 저장했다.
- **막힌 점 / 바꾼 점**: 제공된 KOSIS URL은 origin→destination OD flow가 아니라 지역별 총전입, 총전출, 순이동 등 집계 지표를 반환한다. 현재 파라미터는 시군구가 아니라 전국과 17개 시도 수준만 반환한다. 행정안전부 endpoint는 루트 호출에서 HTTP 500, 추정 operation path에서 403/404가 발생해 수집하지 못했고 `data/mois-ppltn-data-stus-fetch-status.json`에 기록했다.
- **배운 것 / 다음**: bird-eye flow map의 실제 흐름선에는 KOSIS `DT_1B26003_A02` 같은 출발지→도착지 행렬 데이터가 필요하다. 이번 KOSIS 데이터는 유입·유출 허브 크기나 배경 지표로는 쓸 수 있지만, 지역 간 흐름선의 원천 데이터로는 부족하다.

### 2026-06-27 행안부 OD 데이터 재수집
- **정한 것 / 한 것**: 행정안전부 `ppltnDataStus/selectPpltnDataStus` API의 필수 요청변수(`mvinAdmmCd`, `mvtAdmmCd`, `srchFrYm`, `srchToYm`, `lv`)를 적용해 2026년 5월 시도 단위 17x17 origin→destination 행렬을 수집했다.
- **왜**: 전국 bird-eye flow map의 실제 흐름선에는 지역별 집계가 아니라 출발지→도착지 쌍별 이동량이 필요하기 때문이다.
- **어떻게**: `lv=1`, `type=json`, `srchFrYm=202605`, `srchToYm=202605`로 17개 시도 모든 조합 289쌍을 호출했다. 정규화 파일은 `data/mois-ppltn-data-stus-sido-od-202605.csv`, 대시보드용 flow 파일은 `data/mois-sido-flows.csv`, 메타데이터는 `data/mois-ppltn-data-stus-sido-od-202605-metadata.json`에 저장했다.
- **막힌 점 / 바꾼 점**: 이전 실패 원인은 operation path가 아니라 필수 요청변수 누락이었다. `/selectPpltnDataStus`는 맞는 경로이며, 루트 endpoint 직접 호출은 계속 HTTP 500이 난다.
- **배운 것 / 다음**: `mvt*` 필드는 전출지(origin), `mvin*` 필드는 전입지(destination)로 해석해야 한다. 이 데이터는 flow map 선 데이터로 바로 사용할 수 있다.

### 2026-06-27 남한 베이스맵 arc 시각화 설계 반영
- **정한 것 / 한 것**: 필수 산출물 구조와 3시간 MVP 범위를 정리했다.
- **왜**: 팀별 결과물을 같은 구조로 남겨 이후 사례집과 워크플로 라이브러리로 재사용하기 위해서다.
- **어떻게**: 반응형 질문 답변을 표준 필드로 정규화해 PLAN.md, workshop.json, WORKFLOW_ANALYSIS.md, CASE_STUDY.md, MEMORY.md에 기록했다.
- **막힌 점 / 바꾼 점**: 없음
- **배운 것 / 다음**: 사용자가 PLAN.md 기준으로 MVP를 구현하고, 완료 후 검수 포인트와 기록을 보완한다.

### 2026-06-27 웹앱 구현
- **정한 것 / 한 것**: `PLAN.md` 기준으로 `index.html`을 남한 베이스맵 arc flow map 웹앱으로 재구현했다. 기본 입력은 `data/mois-ppltn-data-stus-sido-od-202605.csv`이며 같은 시도 내부 이동은 화면에서 제외한다.
- **왜**: MVP 성공 기준이 단순 표/필터가 아니라 한국(남한) 지도 위에 출발지→도착지 이동 유량을 솟는 곡선 arc로 보여주는 것이기 때문이다.
- **어떻게**: 정적 HTML/CSS/JS 안에서 MOIS OD CSV를 fetch하고, 시도별 고정 좌표와 단순 남한 윤곽 베이스맵 위에 cubic bezier arc를 그렸다. 선 굵기는 이동량, 노드 크기는 총 유입·유출 허브 강도, 색상은 향후 특성 레이어 확장을 위한 슬롯으로 분리했다. README와 data/README도 현재 데이터 구조에 맞게 갱신했다.
- **막힌 점 / 바꾼 점**: 브라우저 검증을 위해 로컬 서버가 필요했다. 샌드박스 포트 바인딩과 Playwright 브라우저 캐시 버전 문제로 권한 승인 후 Chromium을 설치해 검증했다.
- **배운 것 / 다음**: 데스크톱과 모바일에서 콘솔 오류, 요청 실패, 가로 오버플로 없이 렌더링됐다. 발표자료용 공개 캡처는 `presentation-assets/result_screenshot.png`에 저장했다.
