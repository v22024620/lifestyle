# LOP (Lifestyle Ontology Partner) 개발 계획 (애플 PM 관점)

## 0. 미션과 KPI
- 미션: 웰니스 스튜디오(PT, 필라테스, 복싱, 재활 등)의 결제/정산/운영 데이터를 온톨로지 기반으로 정제하여, LOP 수준의 투명성과 사용자 경험을 제공하는 커머스 파트너.
- 핵심 가치: 투명한 커머스 레이어, 온톨로지 기반 인텔리전스, 소비자 보호 강화.
- KPI: (1) 호출당 최소 3개 이상의 의미 있는 인사이트, (2) 시뮬레이션 응답 성공률 95%+, (3) 월 장애율 0.1% 미만.

## 1. 기술 스택
- 언어/런타임: Python 3.11
- 서버: FastAPI + Uvicorn
- Retrieval: GraphRAG(GraphDB + Neo4j) + Chroma Vector DB
- 온톨로지/그래프: rdflib(TTL/RDF 파싱), GraphDB(SPARQL), Neo4j(py2neo)
- LLM: LLMClient(OpenAI 호환) + stub fallback
- 기타: pydantic, httpx, SPARQLWrapper, pytest, logging/structlog(로드맵)

## 2. 실행 구성
1) 데이터 로딩: data/ontology/extensions/lop-lifestyle/fibo_core_subset.ttl + data/ontology/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl을 OntologyService로 병합하고 CSV 샘플은 Chroma/Neo4j 부트스트랩에 활용.
2) Retrieval: GraphRAGService가 SPARQL/Neo4j/Vector 검색을 통합해 역할별 콘텍스트 생성.
3) Multi-Agent: Insight·Risk·Recommendation·Strategy·Explainer 에이전트를 Orchestrator가 제어.
4) API·Streamlit: FastAPI/Streamlit으로 인사이트·시뮬레이션을 노출.
5) 시뮬레이션 데이터: data/simulations/generate_simulation_data.py 실행으로 공급자·운영자·고객 CSV와 provider_metrics.ttl을 생성, GraphDB·Neo4j·Vector 시드에 활용.
## 3. 디렉터리 구조
```
lop/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── studios.py
│   │       ├── insights.py
│   │       └── simulate.py
│   ├── services/
│   │   ├── graphrag_service.py
│   │   ├── vector_service.py
│   │   ├── ontology_service.py
│   │   ├── neo4j_service.py
│   │   ├── agent_orchestrator.py
│   │   └── recommendation_simulator.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── wellness_insight_agent.py
│   │   ├── risk_guard_agent.py
│   │   ├── revenue_architect_agent.py
│   │   ├── strategy_framework_agent.py
│   │   └── consumer_explainer_agent.py
│   ├── models/
│   │   ├── studio.py
│   │   ├── transaction.py
│   │   ├── settlement.py
│   │   └── common.py
│   └── utils/
│       ├── logging.py
│       ├── llm_client.py
│       └── cache.py
├── data/
│   ├── fibo/
│   │   ├── data/ontology/extensions/lop-lifestyle/fibo_core_subset.ttl
│   │   └── data/ontology/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl
│   └── samples/
│       ├── studios.csv
│       ├── sessions.csv
│       ├── transactions.csv
│       └── settlements.csv
├── requirements.txt
└── streamlit_app.py
```

## 4. 온톨로지 & 데이터 요구사항
- 코어 개념: WellnessStudio, Trainer, SessionPackage, MembershipContract, PaymentPlan, BodyMetric, RiskEvent, WellnessInsurance.
- TTL 세트: data/ontology/extensions/lop-lifestyle/fibo_core_subset.ttl, data/ontology/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl.
- OntologyService
  - `load_ontologies()`: TTL 로딩 및 네임스페이스 등록.
  - `merge_graphs()`: 병합 그래프 반환.
  - `sparql_query(query: str)`: GraphDB endpoint 호출(`GRAPHDB_ENDPOINT`).
  - `to_neo4j_payload()`: Neo4j 노드/관계 export.

## 5. Retrieval & 캐시 전략
- VectorService: Chroma 초기화, 샘플 CSV 임베딩/검색, studio 단위 UoW 메타데이터 저장.
- GraphRAGService: SPARQL + Cypher + Vector 결과를 결합한 Context builder. TTL 캐시(studio-id 기반).
- 캐싱: TTLCache(기본 5분 / max 5 key)로 Orchestrator 응답 재사용.

## 6. 멀티 에이전트 설계
- BaseAgent: 공통 LLMClient + 한국어 프롬프트 가드 적용.
- WellnessInsightAgent: 수강권 소진률, 재등록률, 강사별 매출/세션 지표.
- RiskGuardAgent: 환불 급증, 보험 만료, 정산 지연, 신고 데이터 기반 위험 시그널.
- RevenueArchitectAgent: 요금제/예치금/보험 시뮬레이션 → RecommendationSimulator 연동.
- StrategyFrameworkAgent: GraphRAG 컨텍스트로 PESTEL/Porter/McKinsey 7S 요약.
- ConsumerExplainerAgent: 소비자 보호/실행 요약을 일반 화법으로 제공.
- AgentOrchestrator: GraphRAG context → 모든 agent 실행 → trace id 포함 JSON 반환.

## 7. API & Streamlit
- FastAPI 엔드포인트
  - `POST /studios/{studio_id}/insights`: body `{ "query": "optional" }` → agents 파이프라인 응답.
  - `POST /simulate/plan`: `studio_id`, `current_plan`, `candidate_plans`, `period`, `insurance`, `deposit` 옵션.
  - `GET /health`
- Streamlit
  - 타이틀: "LOP – Lifestyle Ontology Partner"
  - 좌측: 스튜디오 ID, 질의, 플랜/보험 옵션 입력.
  - 우측: 인사이트 카드, 리스크 그래프, 추천, 전략, 시뮬레이션 영역.
  - 데모 경고: 실제 Graph/LLM/시뮬레이터 연결 전 Stub 안내.

## 8. 운영 요구사항
- 모든 핵심 함수/클래스 docstring 필수.
- LLM 호출은 LLMClient stub/default 사용, 키 없을 경우 예외 없이 한국어 stub.
- 로깅: structured log(trace_id, studio_id, agent, latency).
- 테스트: pytest + faker/mocker로 그래프/LLM I/O 대체.
- 설정: `config.py`에서 GraphDB/Neo4j/Chroma/LLM endpoint 및 캐시 TTL 등 관리.

## 9. 로드맵
1) 데이터/온톨로지: 웰니스 확장 TTL, 샘플 CSV(studios/sessions/transactions/settlements) 작성.
2) Retrieval: VectorService + GraphRAGService 구현, 캐시 레이어.
3) Agents: BaseAgent 한국어 가드, 5개 에이전트 + Orchestrator, RecommendationSimulator stub.
4) API: FastAPI 라우팅, `/studios/{id}/insights`, `/simulate/plan`, `/health` mock 응답.
5) Streamlit: LOP 브랜딩 UI, agent/simulator 연동.
6) 운영: 로깅/모니터링, pytest 스위트, 배포 파이프라인 준비.

## 10. 리스크 & 완화책
- 그래프/온톨로지 동기화 지연 → TTL/CSV 기반 로컬 fallbacks.
- 웰니스 업종별 데이터 편차 → 샘플 데이터 다양화, schema validation.
- 소비자 보호 요구사항 변화 → RiskAgent 규칙/LLM 프롬프트를 버전 관리.
- 외부 의존성(OpenAI, GraphDB) 불가용 → stub/로컬 모드 유지, 재시도/backoff 로직 적용.

