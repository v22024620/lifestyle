# Simulation Data (LOP Rebuild)

`generate_simulation_data.py`는 재구축된 LOP 온톨로지 스키마를 따르는 CSV 3종과 Provider Metric TTL을 생성합니다.

| 파일 | 주요 컬럼 | 설명 |
| --- | --- | --- |
| `provider_metrics.csv` | `week_start`, `studio_id`, `program_id`, `agreement_id`, `avg_daily_sessions`, `engagement_score`, `anomaly_tag` | 스튜디오별 주차 KPI. `datasets/provider_metrics.ttl`로 직렬화됨. |
| `operator_dashboard.csv` | `week_start`, `activation_rate`, `settlement_success_rate`, `loan_balance_krw`, `policy_focus` | HQ 운영 지표. |
| `customer_insights.csv` | `member_id`, `studio_id`, `program_id`, `segment`, `engagement_score`, `recommended_offer` | 고객 세그먼트 및 리텐션 액션. |

## 실행
```
python data/simulations/generate_simulation_data.py
```
- 실행 시 `data/ontology/datasets/provider_metrics.ttl`도 생성되며, `lopsim:ProviderMetric` 클래스와 LOP 핵심 개념을 연결합니다.
