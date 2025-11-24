# LOP 온톨로지 디렉터리 및 통합 계획

edmcouncil/fibo 저장소 최상위 구조(be, bp, cae, der, fbc, fnd, ind, loan, md, sec, etc)를 그대로 따르면서 LOP 기획 요구사항을 담은 디렉터리와 통합 시나리오를 정의합니다.

## 1. 디렉터리 구조(데이터 관점)
```
data/
└─ ontology/
   ├─ md/                      # Metadata & catalog (fibo/ontology/Metadata)
   │  ├─ LOPFitness-Metadata.ttl
   │  └─ catalog-index.md
   ├─ fnd/                     # Foundations 서브셋
   │  ├─ Agents/LOPAgents.ttl
   │  ├─ Arrangements/LOPContracts.ttl
   │  └─ DatesAndTimes/LOPTime.ttl
   ├─ be/                      # Business Entities
   │  ├─ Organizations/Studios.ttl
   │  └─ FunctionalEntities/TrainerNetworks.ttl
   ├─ bp/                      # Business Processes
   │  └─ Engagements/ProgramLifecycle.ttl
   ├─ fbc/                     # Financial Business & Commerce
   │  ├─ Products/FitnessSubscriptions.ttl
   │  └─ Accounting/Settlement.ttl
   ├─ cae/                     # Contracts & Agreements
   │  └─ ProgramParticipationAgreement.ttl
   ├─ der/                     # Derivatives & risk exposure → KPI 기반 파생지표
   │  └─ FitnessRiskDerivedMetrics.ttl
   ├─ ind/                     # Industry extensions (Insurance/Healthcare)
   │  └─ Insurance/FitnessRisk.ttl
   ├─ loan/                    # Loan & credit (스튜디오 설비 금융 모델)
   │  └─ StudioCapexLoans.ttl
   ├─ sec/                     # Securities (구독 수익 증권화 가능성)
   │  └─ FitnessReceivablesSecuritization.ttl
   ├─ extensions/
   │  ├─ lop-lifestyle/
   │  │  ├─ LOPFitness-Core.ttl
   │  │  ├─ LOPFitness-Programs.ttl
   │  │  └─ LOPFitness-Individuals.ttl
   │  └─ mappings/
   │     ├─ neo4j-schema-mapping.yml
   │     └─ graphdb-load-order.txt
   ├─ datasets/
   │  ├─ SGANG01.ttl
   │  ├─ SBRCH02.ttl
   │  └─ risk-events.ttl
   ├─ pipelines/
   │  ├─ rdflib_loader.py
   │  ├─ graphdb_seed.sh
   │  └─ neo4j_ingest.cypher
   └─ README.md
```
- `md` 폴더는 FIBO Metadata(카탈로그, 버전, 배포)와 동일한 역할을 하며 모든 모듈의 `owl:imports` 루트입니다.
- 기존 `data/fibo/fibo_core_subset.ttl`, `fibo_lifestyle_extension.ttl`은 `extensions/lop-lifestyle`로 이동 후 README에서 레거시 경로 안내.

## 2. LOP 전용 모듈 정의
| 계층 | LOP 활용 포인트 |
| --- | --- |
| `fnd` | LOP ID 기반 계약 주체, 기간, 장소를 표준화. `LOPLegalEntity`, `LOPContractParty`, `LOPTimeInterval` 클래스 제공. |
| `be` | WellnessStudio, LOPFitnessDivision, TrainerNetwork를 `LegalEntity`/`FunctionalEntity`로 선언. SKOS 레이블로 GraphRAG 설명문에 활용. |
| `bp` | 프로그램 기획/운영 프로세스(런칭, 온보딩, KPI 리뷰) 모델링. BPMN-like 단계와 KPI 이벤트를 RDF 시퀀스로 표현. |
| `cae` | ProgramParticipationAgreement, Revenue Share Agreement 등 계약 조건을 명세. Clause별 KPI/벌칙 속성 포함. |
| `fbc` | 구독/정산/환불/보험금 흐름을 MonetaryAmount, Account, Transaction 패턴으로 표현. ISO 4217 화폐 코드 유지. |
| `der` | KPI 파생지표(Activation Momentum, Churn Risk Index)를 파생상품 클래스에 매핑해 리스크 관리 시나리오 지원. |
| `ind` | FitnessRiskEvent, InsuranceCoverage 요소를 보험 도메인 용어와 연결해 HealthKit 기반 사고 대응에 활용. |
| `loan` | 스튜디오 설비 투자, 리스 계약을 LoanAgreement 패턴으로 모델링하여 파트너 재무 구조 분석. |
| `sec` | 구독 수익 유동화 가능성을 위해 Receivable-backed Securities 구조 정의(미래 파트너십 KPI 연계). |

## 3. 온톨로지 산출물 및 도구 연계
- **TTL/OWL 산출물**: 각 디렉터리별 최소 1개 모듈을 작성하고 `md/LOPFitness-Metadata.ttl`에 등록. `extensions/lop-lifestyle`은 실제 LOP 데이터(스튜디오, KPI)를 `owl:imports`로 묶는 번들을 제공.
- **rdflib** (`pipelines/rdflib_loader.py`): Metadata → FND → BE → BP/CAE → FBC → DER/IND/LOAN/SEC → Extensions 순으로 로딩, `rdflib.compare.to_isomorphic`로 일관성 검사.
- **GraphDB** (`graphdb_seed.sh`): edmcouncil 샘플처럼 `/rest/repositories/{repo}/statements` 호출. 로딩 순서를 `mappings/graphdb-load-order.txt`로 자동화.
- **Neo4j** (`neo4j_ingest.cypher` + `neo4j-schema-mapping.yml`): `n10s.rdf.import.fetch` 사용, LOP KPI 속성을 Neo4j Property로 매핑(예: `af:activationRate -> activation_rate`).
- **GraphRAG**: `datasets/*.ttl`을 SPARQL로 질의해 LLM 콘텍스트 생성. SKOS 정의, KPI 메트릭을 텍스트로 추출 후 Chroma 임베딩 생성.
- **GraphDB ↔ Neo4j 싱크**: GraphDB에 저장된 계약/정산 triples를 Neo4j ETL 파이프라인에서 정기적으로 pull, LOP 기획자가 리스크 뷰를 360도로 확인.

## 4. LOP 기획자 관점 로드맵
1. **주 1**: `md`, `fnd`, `be` 최소 스켈레톤 작성, 네임스페이스/버전 정책 확정, rdflib 로더 PoC.
2. **주 2**: `bp`, `cae`, `fbc` 모듈 완성, ProgramParticipationAgreement와 Settlement 모델을 GraphDB에 적재.
3. **주 3**: `der`, `ind`, `loan`, `sec` 초기 스키마 작성, KPI 파생지표와 재무 시나리오를 Neo4j로 이관.
4. **주 4**: `extensions/lop-lifestyle`에 실데이터(5개 스튜디오, 리스크 이벤트) 등록, datasets 추출 및 GraphRAG 파이프라인 연결.
5. **주 5**: 그래프 질의 템플릿(정산 이상 탐지, KPI 트렌드)을 마련하고 LOP 사업 리뷰에 활용.

## 5. 즉시 실행 항목
- `data/ontology` 트리 생성 후 README에 edmcouncil 디렉터리 대응표 기재.
- 기존 TTL 파일 이동 및 `owl:imports` 경로 업데이트.
- rdflib/GraphDB/Neo4j 파이프라인 스크립트 템플릿 생성, CI에서 `riot` 혹은 `rapper` 검증 스텝 추가.
- GraphRAG 서비스 구성요소(`app/services/graphrag_service.py`)에서 새로운 datasets 경로를 참조하도록 환경설정 갱신.