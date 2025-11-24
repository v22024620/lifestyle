# Lifestyle Service Architecture

서비스 아키텍처 다이어그램 요약(LOP 기획 관점)
- 서비스 구성: GraphRAG 기반 Insight & Strategy, Risk Guard & Ops Control, Recommendation & Simulation 모듈이 멀티 에이전트로 묶여 LOP 기획 플로우를 지원합니다.
- 프런트엔드: Streamlit 대시보드에서 스튜디오 선택, KPI 카드, 시뮬레이션 결과를 제공합니다.
- 백엔드: FastAPI가 Ontology Service·GraphRAG·Recommendation Simulator를 묶어 `/studios/{id}/insights`, `/simulate/plan` 등 API로 노출합니다.
- 데이터베이스: rdflib(GraphDB 호환) + ChromaDB(벡터) + Neo4j(그래프) 조합으로 FIBO TTL, CSV 샘플, 그래프 컨텍스트를 보관하고, Jenkins 없이 로컬 배포 스크립트로 관리합니다.
- 데이터 소스: FIBO TTL, 샘플 CSV(스튜디오·세션·거래·정산), 환경 변수 기반 GraphDB/Neo4j 연결, Streamlit 입력.
- LLM: OpenAI(ChatGPT) API를 사용하는 LLMClient가 5개 에이전트를 구동합니다.
- BI/UI: Streamlit KPI 카드와 향후 Tableau 연동을 염두에 둔 구조입니다.

Tech Stack
- LLM: OpenAI(ChatGPT)
- BI/UI: Streamlit (추가 Tableau 연동 가능)
- CI/CD: 로컬 스크립트 기반 배포(추후 Jenkins 연동 가능)
- IDE: Visual Studio Code + Python
- Embedding/ML: Hash 기반 임베딩 + GraphRAG + rdflib (필요 시 SciPy 등 경량 수학 라이브러리 활용)
## Neo4j GraphRAG 파이프라인
- `app/services/neo4j_templates.py`: 엔티티 검색, 경로 탐색, 증거 수집을 위한 파라미터화된 Cypher 템플릿을 정의합니다.
- `app/services/neo4j_reasoner.py`: 공식 Neo4j 드라이버를 사용해 템플릿을 실행하고 엔티티·경로·증거 번들을 반환합니다.
- `Neo4jReasoner.run_pipeline(keywords, start_id, end_id, studio_id)`: 세 단계를 연속 수행해 GraphRAG 컨텍스트를 구성합니다.
- `requirements.txt`에 `neo4j` 드라이버가 추가되었으므로 bolt URI/자격 정보만 주입하면 실시간 질의가 가능합니다.
