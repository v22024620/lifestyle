# data/ontology README

이 디렉터리는 edmcouncil/fibo의 최상위 폴더(be, bp, cae, der, fbc, fnd, ind, loan, md, sec, etc)를 LOP 시나리오에 맞춰 매핑한 구조입니다. 각 폴더는 동일한 축약어를 그대로 사용하여 `owl:imports` 경로가 GitHub 원본과 1:1 대응되도록 설계했습니다.

| 폴더 | FIBO 대응 | LOP 용도 |
| --- | --- | --- |
| `md/` | Metadata | 네임스페이스/버전/카탈로그 정의(LOPFitness-Metadata.ttl 등) |
| `fnd/` | Foundations | 계약 주체, 시간, 장소, 계정 등 기본 클래스 확장 |
| `be/` | Business Entities | Wellness Studio, Trainer Network, LOPFitnessDivision 등의 조직 표현 |
| `bp/` | Business Processes | 프로그램 라이프사이클, KPI 리뷰 플로우 모델링 |
| `cae/` | Contracts & Agreements | ProgramParticipationAgreement 등 계약 조건 정의 |
| `fbc/` | Financial Business & Commerce | 구독, 정산, 환불, 보험료 흐름 표현 |
| `der/` | Derivatives | KPI 파생지표/리스크 시나리오 정의 |
| `ind/` | Industry | 보험/헬스 도메인의 FitnessRiskEvent, Coverage 매핑 |
| `loan/` | Loans | 스튜디오 CAPEX/리스 금융 계약 모델링 |
| `sec/` | Securities | 수익 유동화, Receivable-backed 구조 탐색 |
| `extensions/lop-lifestyle` | 제품별 확장 | 실측 KPI, 스튜디오 인스턴스, 기존 `fibo_*` TTL 이동 위치 |
| `extensions/mappings` | 로딩 보조 | Neo4j/GraphDB 매핑, 로드 순서 관리 |
| `datasets/` | 그래프 투영 | 스튜디오별 TTL 스냅샷, 리스크 이벤트 추출본 |
| `pipelines/` | 적재 파이프라인 | rdflib 검사, GraphDB/Neo4j 적재 스크립트 |

## 마이그레이션 메모
- 기존 `data/fibo/fibo_core_subset.ttl`, `fibo_lifestyle_extension.ttl`을 `extensions/lop-lifestyle/`로 이동했습니다.
- 향후 새 모듈은 해당 계층 폴더 내에 `LOPFitness-*.ttl` 이름으로 추가하고, `md/LOPFitness-Metadata.ttl`의 catalog에서 import 순서를 관리합니다.
- `pipelines/`의 스크립트는 Metadata → FND → BE → BP/CAE → FBC → DER/IND/LOAN/SEC → Extensions 순으로 TTL을 처리하도록 설계합니다.
- `datasets/provider_metrics.ttl`은 `data/simulations/generate_simulation_data.py`가 생성하는 공급자 KPI 스냅샷으로, GraphDB·Neo4j 초기 시뮬레이션에 활용합니다.
