# LOP Dashboard UX Redesign — `dashboard.md`  
(Apple Fitness+ 디자이너 관점 고도화 버전)

---

## 0. 컨셉 & 톤

### 0.1 제품 컨셉

- 서비스명: **LOP (Lifestyle Ontology Partner)**
- 브랜드 레퍼런스:
  - **Apple Fitness+**(맑고 간결한 운동 경험)
  - **Apple Health / Wallet**(데이터를 “안심·투명하게” 보여주는 UI)
- 핵심 미션:
  > “그래프·온톨로지 기반의 복잡한 인사이트를  
  > **운영사 / 스튜디오 / 회원**이 각각 *한눈에* 이해할 수 있도록  
  > Apple Fitness+ 수준의 단순함과 정서적 안전감으로 전달하는 것.”

### 0.2 디자인 톤 & 원칙

1. **Calm & Clear**  
   - 데이터는 많지만, 화면은 “조용하고 이해하기 쉬운” 상태를 유지한다.  
   - 한 화면에 “결정 포인트 1–2개”만 강조한다.

2. **Trust & Care**  
   - 리스크/경고도 “공포감”이 아닌 “케어·코칭” 톤으로 전달.  
   - 텍스트 카피는 Apple Fitness+의 “친절한 코치” 느낌.

3. **Rhythm & Whitespace**  
   - 세로로는 “섹션 3단계(헤더 / 카드 영역 / 세부·원본 영역)”  
   - 가로로는 “2~3열 그리드”만 사용해 시선을 유도.

---

## 1. 기술 컨텍스트 (변경 금지 블록)

- 프로젝트: `langchain-kr-main/lifestyle`
- 프론트엔드: `streamlit_app.py` (단일 앱, 멀티 뷰)
- 백엔드:
  - Neo4j / GraphDB + TTL 기반 GraphRAG
  - 멀티 에이전트 (운영사 / 스튜디오 / 고객)
  - OpenAI LLM 연동 (이미 정상 동작)
- 이번 작업 범위:
  - **백엔드·에이전트 로직은 건드리지 않는다.**
  - `streamlit_app.py`의 **레이아웃·스타일·텍스트·뷰 구조만 개선**한다.

---

## 2. 글로벌 프레임워크

### 2.1 페이지 설정

`streamlit_app.py` 최상단:

- `st.set_page_config` 적용
  - `page_title="LOP Dashboard"`
  - `page_icon="💫"`
  - `layout="wide"`

### 2.2 공통 디자인 시스템 (CSS 토큰 수준 정의)

`CUSTOM_CSS`에 다음 컨셉을 반영:

- **배경**
  - 앱 배경: `#f5f5f7` (Apple 시스템 앱 계열 톤)
- **카드**
  - 배경: `#ffffff`
  - 모서리: `border-radius: 18px`
  - 그림자: `0 18px 45px rgba(15, 23, 42, 0.04)`
  - 경계: `1px solid rgba(148, 163, 184, 0.28)`
- **타이포**
  - 폰트: `-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif`
  - 헤더(대제목): 36–40px, weight 800
  - 섹션 제목: 18–20px, weight 700
  - 라벨: 11–12px, uppercase, letter-spacing 0.08em
- **코드/JSON 박스**
  - 배경: `#0b1120`
  - 폰트: 모노스페이스
  - 모서리: `border-radius: 14px`
- **프레임 클래스**
  - `.lop-header-title`
  - `.lop-header-subtitle`
  - `.lop-card`
  - `.lop-section-title`
  - `.lop-label-muted`
  - `.lop-json-box`
- **Streamlit 기본 요소**
  - `#MainMenu`, `footer` 숨김 → 제품 데모처럼 보이게

---

## 3. 뷰 아키텍처 (3 Persona)

Streamlit 내에서 **3개의 뷰 함수**로 분리:

- `render_operator_view(operator_insight)`  
  → 운영사 Command Center
- `render_studio_view(studio_insight)`  
  → 스튜디오 Console
- `render_member_view(member_insight)`  
  → 회원(End User) Trust Portal

뷰 선택:

- 방법 1: `st.sidebar.radio("View", ["운영사", "스튜디오", "회원"])`
- 방법 2: 상단 `st.tabs(["운영사", "스튜디오", "회원"])`

※ Codex는 기존 `view` 분기 로직을 이 구조로 정리한다.

---

## 4. 운영사 Command Center (Operator View)

### 4.1 목표

- 플랫폼 HQ / 본사 운영팀이 보는 **“상단 관제 화면”**.
- Neo4j / GraphDB 기반 리스크 + 전략 코어 인사이트를 한 눈에 보여준다.
- **Apple Fitness+의 “트레이닝 요약 카드” 느낌**으로,  
  리스크도 “조용하게”, 그러나 “결정은 빠르게” 할 수 있게 만든다.

### 4.2 레이아웃 구조

1. **SECTION A — 헤더**
   - `운영사 Command Center` (대제목)
   - 서브카피 예:  
     > “스튜디오 네트워크 전반의 리스크와 전략을  
     > 그래프 기반으로 요약한 운영 대시보드입니다.”

2. **SECTION B — 상단 KPI 카드 (3개)**  
   `st.columns(3)` + 각 컬럼 안에 `.lop-card` 배치

   - 카드1: **Indexed Docs**
     - 값: `operator_insight['indexed_docs']`
     - 캡션: “Vector DB에 인덱싱된 문서 수”
   - 카드2: **Primary Signal**
     - 값: `Graph / Text / Hybrid` 등
     - 캡션: “이번 인사이트의 핵심 데이터 소스”
   - 카드3: **Sample AOV**
     - 값: 평균 거래금액 또는 `-`
     - 캡션: “Apple Fitness+ 샘플 거래 기준”

3. **SECTION C — 네트워크 리스크 Pulse (차트 + 요약)**  
   `st.columns([2.2, 1.2])`

   - **좌측 카드 (Risk Pulse Chart)**
     - 타이틀: `네트워크 리스크 Pulse`
     - 바 차트: `graph_anomaly_suspected`, `ontology_complex_relation` 등
     - 느낌: Apple Fitness+에서 “하루 활동 링” 보여주는 수준의 **간단하고 즉각적인 그래프**
   - **우측 카드 (Risk & Strategy Summary)**
     - 타이틀: `오늘의 운영 요약`
     - 본문:
       - `narrative_risk` (리스크 한 단락)
       - 구분선
       - `narrative_strategy` (전략 제안 한 단락)
     - 카피 톤:
       - “위험합니다” 보다는  
         “이 영역을 한 번 더 점검하면 좋겠습니다” 톤

4. **SECTION D — 원본 프레임 (JSON Transparency)**

   - 하단 전체를 `.lop-card`로 감싸고  
   - 좌/우 2열:
     - 좌: `리스크 프레임 (Risk JSON)`
     - 우: `전략 프레임 (Strategy JSON)`
   - JSON은 `<pre class="lop-json-box">...</pre>` 형태로 표시  
   - 이 섹션은 **연구자·개발자·내부 검증용**이며,  
     제품 데모에서도 “투명성” 메세지를 준다.

---

## 5. 스튜디오 Console (Studio View)

### 5.1 목표

- **개별 피트니스 스튜디오 매니저/소유자**를 위한 화면.
- Apple Fitness+의 “나의 워크아웃 요약”처럼,  
  “내 스튜디오 상태”를 직관적인 카드와 경량 차트로 보여준다.
- HQ용 리스크·전략보다 **실행 중심** (예약, 매출, 구독자 흐름).

### 5.2 레이아웃 구조

1. **SECTION A — 헤더**

   - 예: `Studio Console — AppleFit 강남`
   - 서브카피:  
     > “오늘의 예약, 수익, 프로그램 컨디션을 한 눈에 확인하세요.”

2. **SECTION B — 스튜디오 KPI 카드 (3개)**

   - 카드1: **이번 달 매출**
   - 카드2: **활성 구독자 수**
   - 카드3: **진행 중 프로그램 수 / 트레이너 수**

3. **SECTION C — 프로그램 & 구독 흐름**

   `st.columns([1.5, 1.5])`

   - 좌측: 간단 차트 (예: 프로그램별 참여율 / 시간대별 체크인)
   - 우측: LLM 기반 인사이트 텍스트  
     - 예: “저녁 7시 이후 HIIT 프로그램 수요가 두드러집니다.”  
            “요가 프로그램 재구매 비율이 높습니다.”

4. **SECTION D — 주의 신호 (Light Alerts)**

   - 리스트 형식의 카드:
     - “지난 주 대비 환불 비율이 2% 증가했습니다.”
     - “특정 트레이너 세션 이탈률이 평균보다 높습니다.”
   - Apple Health처럼 **“가벼운 알림” 느낌**으로 요약.

---

## 6. 회원 Trust Portal (Member View)

### 6.1 목표

- **엔드 유저(회원)**가 자신의 운동/구독 현황을 믿고 볼 수 있는 화면.
- Apple Fitness+ 홈 화면처럼 **긍정적·동기부여 중심**.
- 내부 리스크/운영 정보를 숨기고,  
  “나에게 필요한 제안”만 부드럽게 보여준다.

### 6.2 레이아웃 구조

1. **SECTION A — 헤더**

   - 예: `Member Portal — 정민 님`
   - 서브카피:  
     > “최근 활동과 앞으로의 추천 루틴을 한 곳에서 확인하세요.”

2. **SECTION B — 마이 액티비티 카드**

   - 카드1: **이번 달 세션 수**
   - 카드2: **총 운동 시간**
   - 카드3: **목표 달성률 / 추천 목표**

3. **SECTION C — 추천 프로그램 / 트레이너**

   `st.columns(2)`

   - 좌: 추천 프로그램 리스트
     - **제목** + 짧은 이유
   - 우: “다음 한 주를 위한 제안”
     - LLM이 생성한 2–3개의 구체적인 액션 문장

4. **SECTION D — 나의 그래프 요약 (텍스트 중심)**

   - 실제 Neo4j 그래프를 그대로 노출하지 말고,
   - “구독 중인 프로그램 → 자주 이용하는 시간대 → 선호 트레이너”  
     같은 연결 관계를 자연어로 설명.

---

## 7. 카피 톤 가이드 (Apple Fitness+ 스타일)

- 운영사:
  - ❌ “리스크가 심각합니다.”
  - ✅ “이 영역을 한 번 더 점검하면, 네트워크 안정성이 개선될 수 있습니다.”
- 스튜디오:
  - ❌ “매출이 떨어지고 있습니다.”
  - ✅ “지난 달 대비 오후 타임의 예약이 줄어들고 있어요. 타겟 프로모션을 고려해보면 좋겠습니다.”
- 회원:
  - ❌ “운동이 부족합니다.”
  - ✅ “이번 주에는 한 번만 더 세션을 추가해보면 어떨까요? 목표에 더 가까워질 수 있어요.”

---

## 8. Codex 작업 To-do (구체 액션 리스트)

1. `streamlit_app.py`에 `st.set_page_config`와 `CUSTOM_CSS` 추가.
2. 공통 스타일 클래스(`.lop-*`)를 정의하고, 기존 카드/텍스트 위에 적용.
3. 현재 view 분기 코드를:
   - `render_operator_view(...)`
   - `render_studio_view(...)`
   - `render_member_view(...)`
   세 개의 함수로 리팩터링.
4. 운영사 뷰:
   - 상단 헤더 + KPI 3카드 + 리스크 차트 + 요약 카드 + JSON 섹션 구성.
5. 스튜디오 뷰:
   - 스튜디오 KPI 3카드 + 간단 차트 + 인사이트 카드 + 주의 신호 리스트 구성.
6. 회원 뷰:
   - 마이 액티비티 3카드 + 추천 프로그램/액션 카드 구성.
7. 기존 백엔드 호출·에이전트 호출 코드:
   - 변경하지 말고, `*_insight` dict에 담아 각 렌더 함수에 전달되도록 연결.

---

## 9. 최종 기대 상태

이 `dashboard.md`를 반영해 Codex가 리팩터링을 완료하면:

- 현재의 “기능 확인용 프로토타입” 화면이
- **Apple Fitness+ 스타일의 카드형, 조용한 데이터 콘솔**로 변신하고,
- **운영사 / 스튜디오 / 회원** 3 퍼소나의 시점이  
  UX 차원에서 명확하게 분리된다.

백엔드(Neo4j / GraphDB / 멀티 에이전트)는 그대로 유지하면서,  
**포트폴리오/면접에서 바로 보여줄 수 있는 수준의 대시보드**를 목표로 한다.
