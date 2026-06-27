# 실제 지도 베이스맵 + 3D 항로 arc 고도화 설계

날짜: 2026-06-27
대상 파일: `index.html` (단일 정적 HTML), `data/`, `scripts/`

## 목표
현재 손으로 그린 대략적인 한국 모양 블롭(`<path class="land">`)을 **실제 GeoJSON 시도 경계**로 교체하고, 그 베이스맵 위에 **항로 arc만** "위로 솟았다 내려오는" 3D 느낌의 곡선으로 그린다. 3D 지구본 없음, 남한만.

시군구 드릴다운 화면도 실제 시군구 경계 지도로 교체한다.

## 제약
- 외부 런타임 의존성 없음 (순수 정적 HTML 한 파일 유지, `file://` 및 오프라인 동작).
- GeoJSON은 repo에 내장하되 파일 크기를 위해 대폭 간소화.
- 기존 기능 전부 유지: TOP30/80/ALL, 월 슬라이더, 연령·성별 필터, 지역 강조, 허브 노드·라벨, 흐름 리스트/표, 드릴다운/업.

## 데이터 (빌드 1회, `scripts/build_korea_geojson.py`)
입력: southkorea-maps(kostat 2018) `skorea-provinces`, `skorea-municipalities` 원본.

처리:
1. **시도**: 표준 2자리 `code`(11,26,...,50) 보유. CSV 도 코드 앞 2자리와 매칭.
2. **시군구**: 비표준 code라 도 매칭 불가 → **geometric containment**(시군구 중심점이 어느 시도 폴리곤 안에 있는지)로 `province`(시도 풀네임) 태깅.
3. **CSV 이름 매칭(`match` 속성)**: 시군구 이름이 CSV `origin`과 일치하면 그대로. CSV가 시 단위인데 GeoJSON이 구 단위로 분할된 13개 도시는 하드코딩 시→구 표로 각 구에 부모 시 `match` 부여. 인천 `남구`→`미추홀구`. 세종은 단일 feature.
4. **간소화**: Douglas–Peucker로 좌표 축소 + 좌표 소수점 4자리 반올림. 시도 목표 ~100KB, 시군구 목표 ~500KB 이하.

출력: `data/korea-sido.geojson`, `data/korea-sigungu.geojson` (각 feature에 `name`, `code`, `province`, `match` 속성).

## 투영 (인라인, 의존성 없음)
- 경량 Web Mercator 투영 함수(약 20줄): 입력 lon/lat → 화면 x/y.
- 주어진 feature 집합의 bounding box를 SVG viewBox(여백 포함)에 맞춰 `scale`/`translate` 자동 계산(fit-to-bounds).
- 전국 화면: 남한 17개 시도 bounds로 fit. 드릴다운: 선택 도의 시군구 bounds로 fit.
- GeoJSON 폴리곤 path 생성기(약 15줄): Polygon/MultiPolygon → SVG path `d`.

## 노드 좌표
- 하드코딩 `regionPoints` x/y 제거. 각 시도/시군구 노드 좌표 = 해당 feature(또는 `match`로 묶인 feature 집합)의 폴리곤 중심점을 투영한 값.
- `label`(서울, 부산 등 약칭)만 시도 풀네임 키로 유지.

## 렌더링
**베이스맵**: 투영된 시도(또는 시군구) 폴리곤 = 땅 채움 + 경계선 + 드롭섀도우. 기존 `.land`/`.zoom-land` 스타일 계승. 바다 라벨 유지.

**항로 arc (3D 느낌 강화)**:
- 기존 cubic bezier 위로 솟는 곡선 유지(굵기 = 유량).
- 입체감 강화: (a) 정점 부근이 밝은 세로 그라데이션, (b) 지면에 깔리는 그림자 offset 개선, (c) 정점 하이라이트. 베이스맵 위에 arc만 표시.

## 범위 밖
- 신규 데이터 출처/통계 변경 없음. 기존 CSV 그대로 사용.
- 색상 특성 레이어(현 예약 상태) 변경 없음.

## 검증 기준
1. 전국 화면이 실제 남한 시도 경계로 렌더(서울/경기/부산 등 위치가 지리적으로 맞음).
2. arc가 실제 시도 중심점 사이를 잇고 위로 솟았다 내려옴.
3. 도 클릭 → 해당 도의 실제 시군구 경계 지도로 드릴다운, "전국" 버튼으로 복귀.
4. 모든 필터/슬라이더/리스트/표가 기존대로 동작.
5. 외부 네트워크 없이 `file://`에서 동작 (GeoJSON 내장).
