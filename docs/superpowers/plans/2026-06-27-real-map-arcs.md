# 실제 지도 베이스맵 + 3D 항로 arc 구현 계획

> **For agentic workers:** 단일 정적 HTML 프로젝트. 검증은 단위 테스트가 아니라 브라우저 시각/기능 확인.

**Goal:** 손그림 한국 블롭을 실제 GeoJSON 시도/시군구 경계로 교체하고 그 위에 3D 느낌 항로 arc만 그린다.

**Architecture:** 빌드 스크립트가 원본 GeoJSON을 간소화·태깅해 `data/`에 내장. `index.html`은 인라인 Mercator 투영으로 폴리곤과 노드 중심점을 렌더.

**Tech Stack:** Pure HTML/SVG/JS (런타임 의존성 0), Python 3 빌드 스크립트.

## Global Constraints
- 외부 런타임 의존성 금지. `file://`·오프라인 동작.
- 기존 기능 전부 유지: TOP30/80/ALL, 월 슬라이더, 연령·성별 필터, 지역 강조, 허브 노드·라벨, 흐름 리스트/표, 드릴다운/업.
- 남한만. 3D 지구본 없음.

---

### Task 1: 빌드 스크립트로 GeoJSON 데이터 생성
**Files:** Create `scripts/build_korea_geojson.py`, `data/korea-sido.geojson`, `data/korea-sigungu.geojson`

- [ ] 원본 sido/sigungu 다운로드(또는 캐시 사용)
- [ ] 시군구 중심점이 들어가는 시도 폴리곤으로 `province` 태깅 (geometric containment, ray-casting)
- [ ] 분할 13개 시 + 인천 남구→미추홀구 시→구 표로 `match` 속성 부여, 나머지는 `match=name`
- [ ] Douglas–Peucker 간소화 + 좌표 4자리 반올림
- [ ] `data/`에 출력, 크기 확인 (시도 ~100KB, 시군구 <600KB 목표)
- [ ] 검증: feature 수, province 태깅 누락 0, CSV 이름 중 match 미존재 0 출력

### Task 2: index.html — 투영·베이스맵·노드 좌표
**Files:** Modify `index.html`

- [ ] 인라인 Mercator 투영 + fit-to-bounds 함수 추가
- [ ] GeoJSON → SVG path `d` 생성기 추가
- [ ] 시도 GeoJSON fetch, 손그림 `.land` path 2개 제거, 투영된 시도 폴리곤 렌더
- [ ] `regionPoints` x/y → GeoJSON 시도 중심점 투영값으로 계산(라벨만 유지). 도 이름 불일치(강원/전북) 코드 매핑
- [ ] 검증: 브라우저에서 남한 시도 경계 + 노드가 지리적으로 맞게 표시

### Task 3: index.html — 3D 항로 arc 강화
**Files:** Modify `index.html`

- [ ] arc 세로 그라데이션(정점 밝게) defs 추가
- [ ] arc-shadow 지면 그림자 개선
- [ ] 굵기=유량 로직 유지 확인
- [ ] 검증: arc가 실제 중심점 잇고 위로 솟았다 내려옴, 입체감

### Task 4: index.html — 시군구 드릴다운 실제 지도
**Files:** Modify `index.html`

- [ ] 시군구 GeoJSON fetch
- [ ] 드릴다운 시 선택 도의 시군구 폴리곤 fit-to-bounds 렌더
- [ ] 노드 좌표 = match로 묶인 시군구 폴리곤 중심점 투영. phyllotaxis 레이아웃 제거
- [ ] 검증: 도 클릭→실제 시군구 지도, "전국" 복귀, 흐름/표 동작

### Task 5: 전체 검증 & 커밋
- [ ] 브라우저로 전국/드릴다운/필터/슬라이더 전수 확인 (스크린샷)
- [ ] 네트워크 차단 상태 동작 확인(내장 데이터)
- [ ] 커밋
