# Ontology Overview for LOP Planning

## 1. Bloomberg FIBO 기반
- data/ontology/extensions/lop-lifestyle/fibo_core_subset.ttl: Bloomberg FIBO(Financial Industry Business Ontology) 중 법인, 계약, 계정, 거래, 보험, 측정 클래스를 선별한 서브셋입니다.
  - LegalEntity/Person, ContractualAgreement, Account, Transaction, MonetaryAmount, Measurement, InsurancePolicy 등 LOP 파트너 계약·정산을 표현하는 데 필수인 개체만 남겨 애플 생태계 외 파트너와도 통합 가능한 구조입니다.
  - 모든 클래스/프로퍼티는 원본 네임스페이스(https://spec.edmcouncil.org/fibo/...)를 유지해 그래프 병합 및 규제/금융 파트너 협업 시 표준 호환성을 보장합니다.


### FIBO 계층별 역할 (LOP 시나리오)
- **Foundations(FND)**: 계약, 주체(에이전트/조직), 거래, 프로세스, 장소·시간 등 모든 모듈의 골격을 제공하는 기초 계층입니다. LOP에서는 스튜디오 계약, 참여자, 정산 이벤트를 모델링할 때 FND의 Contract, Agent, Place, Date 개념을 그대로 활용합니다.
- **Business Entities(BE)**: 법인과 조직 구조, 지배·소유 관계를 표현합니다. WellnessStudio(법인), LOP Division(서비스 조직), 트레이너(개인) 같은 개체가 BE의 LegalEntity/Ownership/FunctionalEntity 개념에 매핑돼 메타버스·오프라인 사업을 동시에 표현할 수 있습니다.
- **Financial Business & Commerce(FBC)**: 금융 상품과 서비스(계정, 거래, 결제 네트워크, 보험 등)를 담습니다. Revenue share 계정, Usage settlement, Insurance policy 등의 LOP 재무 흐름을 FBC의 Account, Transaction, InsurancePolicy 클래스로 모델링합니다.

#### 핵심 개념 예시
- **Natural Person / Legal Person**: 트레이너나 고객 같은 자연인, LOP Division/WellnessStudio 같은 법인을 구분해 계약 당사자 역할을 명확히 합니다.
- **Contract / Contract Party**: LOPFitnessAlignment, ProgramParticipationAgreement가 해당 개념을 상속하여 계약 조항·발효/만료일·당사자를 표현합니다.
- **Account & MonetaryAmount**: 수익배분 계정, 정산 금액, 환불·차지백 금액을 표준화된 MonetaryAmount 구조로 기록합니다.
- **Transaction / Settlement Instruction / Risk Event**: FBC의 거래 개념을 확장해 Usage settlement, Refund/Chargeback 이벤트, 운영 리스크를 동일 그래프 상에서 추적합니다.

## 2. Lifestyle 확장 (LOP 관점)
- data/ontology/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl은 위 코어 서브셋을 owl:imports하여 LOP 기획 요구에 맞춘 확장입니다.
  - **클래스**: ibo-life:WellnessStudio, Trainer, LOPFitnessAlignment, ProgramParticipationAgreement, EngagementMeasurement, FitnessRiskEvent 등 애플 파트너 네트워크 전용 개념을 정의하되 모두 FIBO 상위 클래스의 
dfs:subClassOf로 연결합니다.
  - **속성**: ppleFitnessTier, ppleCommerceTier, ppleMetricSyncLevel, supportsFitnessPlusPrograms, studioRiskCategory, healthKitOptInRate, itnessPlusActivationRate 등 LOP Watch/HealthKit KPI와 상업 등급을 표준 데이터 안에 주석처럼 담습니다.
  - **인스턴스**: SGANG01(서울 PT), SBRCH02(부산 재활), SINC04(인천 복싱), SDAEG03(대구 필라테스), SGWANG05(광주 모빌리티) 등 5개 스튜디오와 LOP Division의 계약, 계정, 거래, 보험, KPI 측정, 리스크 이벤트를 구체적으로 서술해 GraphRAG/Neo4j에서 바로 컨텍스트로 활용할 수 있습니다.
  - **LOP 시나리오**: 계약(LOPFitnessAlignment), 프로그램 참여(ProgramParticipationAgreement), 계정(Account-SGANG01-Revenue 등), 정산 트랜잭션, Fitness+ KPI(링 완료율, HealthKit opt-in, Active Energy), 리스크 이벤트(환불, 차지백)를 모두 FIBO 타입 안에서 표현하므로 LOP 기획자가 수익·위험·운영 상태를 한 그래프에서 추적할 수 있습니다.

## 3. 서비스 연동 흐름
- pp/services/ontology_service.py: 두 TTL을 rdflib 그래프로 로딩하고 GraphDB SPARQL 질의, Neo4j 적재 payload를 제공합니다. GraphDB가 없을 경우 로컬 그래프가 폴백하며, LOP 기획자는 동일 스키마로 GraphDB/Neo4j 어느 환경에서도 분석을 이어갈 수 있습니다.
- pp/services/graphrag_service.py: LOP 기획자의 질의(스튜디오 ID, 사용자 질문)를 입력받아
  1. SPARQL(온톨로지 triple)
  2. Chroma 벡터(스튜디오 메타·거래 로그)
  3. Neo4j 컨텍스트(계약/이웃 노드)
  를 통합해 LLM 에이전트들이 전략/리스크/추천을 생성할 수 있는 배경 지식을 제공합니다.
- pp/services/agent_orchestrator.py: 애플 기획자 워크플로우를 모델링한 멀티 에이전트 파이프라인으로, 초기화 시 온톨로지를 로드하고 seed_neo4j_from_ontology()를 호출해 Neo4j에도 동일 정보를 투입합니다.

## 4. LOP 기획자 시사점
- **표준 정합성**: 모든 클래스/프로퍼티가 Bloomberg FIBO를 상속하므로, 국내 스튜디오뿐 아니라 글로벌 파트너·금융기관과도 동일 그래프 모델을 공유할 수 있습니다.
- **KPI/리스크 관리**: EngagementMeasurement와 FitnessRiskEvent 등 KPI/리스크 구조가 LOP Watch/HealthKit 지표와 바로 매핑되어, LOP 내부 KPI와 재무 이벤트를 한 곳에서 비교할 수 있습니다.
- **확장 원칙**: 새로운 프로그램/스튜디오를 추가할 때도 FIBO 네임스페이스를 그대로 따르고, LOP 전용 정보는 ibo-life namespace의 Datatype/Object property로만 확장하면 갈라파고스 없이 데이터 품질을 유지할 수 있습니다.
- **운영 시나리오**: GraphDB 미가동 시 로컬 rdflib 그래프가 폴백하므로 개발/기획 환경에서도 LOP 전략 도출을 테스트할 수 있습니다. Neo4j 연결 시 LOP Partnerships division과 스튜디오 간 관계를 그래픽하게 탐색할 수 있습니다.

## 5. 관리 체크리스트
- TTL 수정 시 실제 FIBO 네임스페이스와 prefix를 유지해 향후 GraphDB/Neo4j 통합 시 충돌을 방지합니다.
- LOP KPI/프로그램을 추가할 때는 Lifestyle TTL에만 정의하고, 코어 서브셋은 Bloomberg FIBO 원본 스키마에 맞춰 최소한으로 관리합니다.
- pp/config.py에서 GraphDB/Neo4j/Chroma 경로가 환경 변수(LCP_GRAPHDB_ENDPOINT 등)로 주입되는지 확인해, LOP 기획자가 테스트/운영 환경을 쉽게 전환할 수 있도록 합니다.

## 6. 시뮬레이션 데이터
- data/simulations/generate_simulation_data.py를 실행하면 공급자(provider), 운영자(operator), 고객(customer)용 CSV가 생성됩니다.
  - 공급자: provider_metrics.csv – 스튜디오별 주차 KPI/정산/리스크/이상징후.
  - 운영자: operator_dashboard.csv – 글로벌 KPI, 정책 포커스, Loan 노출 등 본사 지표.
  - 고객: customer_insights.csv – 회원 세그먼트, 참여도, HealthKit 동의 여부, 추천 액션.
- 스크립트는 동시에 data/ontology/datasets/provider_metrics.ttl을 작성해 GraphDB/Neo4j에서 바로 적재 가능한 RDF를 제공합니다.
- 해당 데이터셋은 VectorService(Chroma)와 GraphRAG 증거 구조에 주입돼 공급자·운영자·고객 질문을 시뮬레이션하는 데 사용됩니다.

