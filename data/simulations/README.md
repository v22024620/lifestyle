# LOP 시뮬레이션 데이터

## 생성 방법
- 실행 명령: `python data/simulations/generate_simulation_data.py`
- 입력 기준: `data/samples/studios.csv` + 스크립트 내부 `EXTRA_STUDIOS` 템플릿으로 20개 파트너 시나리오를 합성합니다.
- 출력 파일
  1. `provider_metrics.csv` (100행 이상)
  2. `operator_dashboard.csv` (12행)
  3. `customer_insights.csv` (스튜디오당 25명 → 125행)
  4. `data/ontology/datasets/provider_metrics.ttl`

## 컬럼 정의
### provider_metrics.csv
| 컬럼 | 설명 |
| --- | --- |
| 스튜디오ID | `lop-core` 스튜디오 코드 |
| 주차시작일 | ISO 주차 시작일 |
| 일평균세션 | 해당 주 하루 평균 세션수 |
| 신규회원수 | 신규 가입 회원수 |
| 주간매출KRW | 주간 매출 (원) |
| 예상원가KRW | 주간 비용 추정치 |
| 환불율 | 해당 주 환불 비율 |
| 리스크이벤트수 | 사고/환불 이벤트 수 |
| 헬스킷동기화율 | HealthKit 연결 비율 |
| 건강목표달성율 | 목표 달성도 |
| 장비고장건수 | 장비 장애 건수 |
| 이상징후라벨 | “과다환불/세션급감” 등 태그 |
| 권장조치 | 정책/운영 권고 |
| 대표프로그램 | 시그니처 프로그램 |

### operator_dashboard.csv
글로벌 활성화율, 정산 성공률, HealthKit Opt-in, 파트너 NPS, 오픈 인시던트, 정책 포커스, 평균 Loan 잔액, 신규 프로그램 수 등 운영 본사 관점 KPI를 담습니다.

### customer_insights.csv
회원ID, 스튜디오ID, 프로그램, 세그먼트(액티브워처/회복중/신규/하이리스크), 참여점수, 출석률, 헬스킷동의(동의/비동의), 목표달성도, 평균심박(bpm), 추천액션을 제공합니다.

## RDF 출력
`provider_metrics.ttl`에는 `lop-sim:ProviderMetric` 클래스와 `lop-sim:newMembers`, `lop-sim:goalCompletion`, `lop-sim:equipmentIncidents`, `lop-sim:anomalyTag`, `lop-sim:recommendedAction` 등 속성을 포함합니다. GraphDB/Neo4j 로딩 후 SPARQL·Cypher에서 시뮬레이션 KPI를 바로 조회할 수 있습니다.

## 활용 시나리오
- 공급자 뷰: 멀티에이전트가 주차별 매출/리스크/권장조치 데이터를 이용해 PT·재활·복싱 등 파트너별 보고서를 생성.
- 운영자 뷰: Operator CSV로 정책 포커스(환불/장비/가격/교육)와 Loan 노출량을 추적하고, TTL 데이터를 통해 그래프 질의로 이슈 감지.
- 고객 뷰: 세그먼트·참여도·HealthKit 동의율을 결합해 ConsumerExplainerAgent가 맞춤 케어 메시지를 출력.
