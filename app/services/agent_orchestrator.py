from __future__ import annotations
"""Pipeline orchestrator wiring all agents and services."""
import csv
import time
import uuid
from typing import Any, Dict, List, Optional

from app.config import Settings
from app.services.graphrag_service import GraphRAGService
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.services.neo4j_service import Neo4jService
from app.services.studio_analytics import get_studio_analytics
from app.services.knowledge_service import KnowledgeService
from app.services.skill_registry import SkillRegistry, SkillDefinition
from app.utils.llm_client import LLMClient
from app.utils.cache import TTLCache
from app.models.pipeline import PipelineResult
from app.agents.wellness_insight_agent import WellnessInsightAgent
from app.agents.risk_guard_agent import RiskGuardAgent
from app.agents.revenue_architect_agent import RevenueArchitectAgent
from app.agents.strategy_framework_agent import StrategyFrameworkAgent
from app.agents.consumer_explainer_agent import ConsumerExplainerAgent

DEFAULT_WORKFLOW_LABEL = "Default Flow"
WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Growth Sprint": {
        "label": "Growth Sprint",
        "query": "Identify growth levers for the wellness studio portfolio",
        "knowledge_queries": ["growth", "agentic organization", "revenue acceleration"],
        "description": "GraphRAG + McKinsey growth lessons to accelerate ARPPU.",
    },
    "Risk Review": {
        "label": "Risk Review",
        "query": "Assess payment declines and chargeback safeguards",
        "knowledge_queries": ["safety", "policy", "guardrail"],
        "description": "Combines GuardRail policies with McKinsey safety guidance.",
    },
    "Wellness Expansion": {
        "label": "Wellness Expansion",
        "query": "Plan wellness journey extensions based on life-science best practices",
        "knowledge_queries": ["wellness", "life science", "personalization"],
        "description": "Targets new modalities informed by McKinsey wellness insights.",
    },
}


class AgentOrchestrator:
    """Run full multi-agent pipeline and aggregate outputs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMClient(settings.llm_endpoint, api_key=settings.openai_api_key)
        self.vector = VectorService(settings.chroma_path)
        self.ontology = OntologyService(settings.graphdb_endpoint)
        self.neo4j = Neo4jService(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        self.graphrag = GraphRAGService(self.vector, self.ontology, self.neo4j)
        self.analytics = get_studio_analytics()
        self.knowledge = KnowledgeService(settings.chroma_path)
        self.insight_agent = WellnessInsightAgent(self.llm, analytics_service=self.analytics)
        self.risk_agent = RiskGuardAgent(self.llm, analytics_service=self.analytics)
        self.reco_agent = RevenueArchitectAgent(self.llm)
        self.strategy_agent = StrategyFrameworkAgent(self.llm)
        self.explainer_agent = ConsumerExplainerAgent(self.llm)
        self.cache = TTLCache(ttl_seconds=self.settings.cache_ttl_seconds, max_size=5)
        self.workflow_templates = WORKFLOW_TEMPLATES
        self.registry = SkillRegistry()
        self._bootstrap_vector_samples()
        self.graphrag.seed_neo4j_from_ontology()

    def available_workflows(self) -> Dict[str, Dict[str, Any]]:
        return self.workflow_templates

    def _register_skills(self) -> None:
        self.registry = SkillRegistry()
        skills = [
            SkillDefinition(
                name="graphrag_context",
                description="Graph/Vector/Neo4j context builder",
                inputs=["studio_id", "user_query"],
                outputs=["graph", "vector", "neo4j"],
            ),
            SkillDefinition(name="wellness_insight", description="Studio KPI 요약"),
            SkillDefinition(name="risk_guard", description="위험 시그널 평가"),
            SkillDefinition(name="revenue_architect", description="요금제 추천"),
            SkillDefinition(name="strategy_framework", description="PESTEL/Porter 전략 요약"),
            SkillDefinition(name="consumer_explainer", description="소비자 친화 설명"),
        ]
        for definition in skills:
            self.registry.register(definition)

    def _execute_skill(self, name: str, func, payload: Any) -> Any:
        input_payload = payload if isinstance(payload, dict) else {"input": str(payload)[:160]}
        run_id = self.registry.start_run(name, input_payload)
        start = time.time()
        try:
            result = func(payload)
            latency = time.time() - start
            output_payload = result if isinstance(result, dict) else {"result": str(result)[:200]}
            self.registry.end_run(run_id, output=output_payload, latency_s=latency)
            return result
        except Exception as err:  # pragma: no cover - defensive
            latency = time.time() - start
            self.registry.end_run(run_id, status="failed", error=str(err), latency_s=latency)
            raise

    def _gather_knowledge(self, query: Optional[str], template: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        hints = template.get("knowledge_queries") if template else None
        return self.knowledge.search(query, hints=hints, top_k=(template or {}).get("top_k", 4))

    def _bootstrap_vector_samples(self) -> None:
        """Load sample CSV rows into Chroma/memory to enable demo retrieval."""
        sample_files = [
            ("data/samples/studios.csv", self._build_studio_doc),
            ("data/samples/transactions.csv", self._build_transaction_doc),
            ("data/samples/settlements.csv", self._build_settlement_doc),
            ("data/samples/sessions.csv", self._build_session_doc),
        ]
        rows: List[Dict[str, Any]] = []
        for path, builder in sample_files:
            try:
                with open(path, newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    for raw in reader:
                        doc = builder(raw)
                        if doc:
                            rows.append(doc)
            except FileNotFoundError:
                continue
        if rows:
            self.vector.seed_from_rows(rows, content_key="content")

    def _build_studio_doc(self, row: Dict[str, Any]) -> Dict[str, Any]:
        studio_id = row.get("studio_id") or row.get("id") or "unknown"
        content = (
            f"Studio {row.get('name', studio_id)} offering {row.get('modality', '')} "
            f"program {row.get('signature_program', '')} in {row.get('city', '')}"
        )
        return {
            "id": f"studio-{studio_id}",
            "content": content,
            "metadata": {
                "studio_id": studio_id,
                "category": row.get("category"),
                "city": row.get("city"),
            },
        }

    def _build_transaction_doc(self, row: Dict[str, Any]) -> Dict[str, Any]:
        studio_id = row.get("studio_id") or row.get("merchant_id") or row.get("merchant") or "unknown"
        amount = row.get("amount", "0")
        content = (
            f"Transaction of {amount} for studio {studio_id} on "
            f"{row.get('timestamp', row.get('date', 'n/a'))}"
        )
        return {
            "id": f"txn-{row.get('transaction_id', uuid.uuid4())}",
            "content": content,
            "metadata": {
                "studio_id": studio_id,
                "amount": amount,
                "type": row.get("type", "sale"),
            },
        }

    def _build_settlement_doc(self, row: Dict[str, Any]) -> Dict[str, Any]:
        studio_id = row.get("studio_id") or row.get("merchant_id") or "unknown"
        content = f"Settlement for studio {studio_id} period {row.get('period', '')} amount {row.get('amount', '')}"
        return {
            "id": f"settlement-{uuid.uuid4()}",
            "content": content,
            "metadata": {
                "studio_id": studio_id,
                "amount": row.get("amount", "0"),
                "period": row.get("period", ""),
            },
        }

    def _build_session_doc(self, row: Dict[str, Any]) -> Dict[str, Any] | None:
        studio_id = row.get("studio_id") or row.get("merchant_id")
        if not studio_id:
            return None
        content = (
            f"Session {row.get('session_id')} for studio {studio_id} "
            f"type {row.get('session_type')} status {row.get('attendance_status')}"
        )
        return {
            "id": f"session-{row.get('session_id', uuid.uuid4())}",
            "content": content,
            "metadata": {
                "studio_id": studio_id,
                "trainer_id": row.get("trainer_id"),
                "member_id": row.get("member_id"),
                "body_metric_notes": row.get("body_metric_notes"),
            },
        }

    def run_full_pipeline(
        self,
        user_query: str | None,
        studio_id: str,
        workflow: Optional[str] = None,
    ) -> PipelineResult:
        """Execute pipeline and return aggregated dataclass. Uses TTL cache."""
        template = self.workflow_templates.get(workflow or "")
        effective_query = (template or {}).get("query") or user_query
        applied_workflow = (template or {}).get("label") or workflow or DEFAULT_WORKFLOW_LABEL
        cache_key = (studio_id, effective_query or user_query or "", applied_workflow)
        cached: PipelineResult | None = self.cache.get(cache_key)
        if cached:
            refreshed = cached.refresh(mark_cached=True)
            self.cache.set(cache_key, cached)
            return refreshed

        self._register_skills()
        graph_context = self._execute_skill(
            "graphrag_context",
            lambda payload: self.graphrag.build_context(payload.get("user_query"), payload["studio_id"]),
            {"studio_id": studio_id, "user_query": effective_query},
        )
        knowledge_refs = self._gather_knowledge(effective_query or user_query, template)
        graph_context["knowledge"] = knowledge_refs
        graph_context["workflow"] = applied_workflow

        insight = self._execute_skill("wellness_insight", self.insight_agent.run, graph_context)
        risk = self._execute_skill("risk_guard", self.risk_agent.run, graph_context)
        recommendation = self._execute_skill("revenue_architect", self.reco_agent.run, graph_context)
        strategy_payload = {**graph_context, "insight": insight, "risk": risk, "recommendation": recommendation}
        strategy = self._execute_skill("strategy_framework", self.strategy_agent.run, strategy_payload)
        explanation_payload = {
            "insight": insight,
            "risk": risk,
            "recommendation": recommendation,
            "strategy": strategy,
        }
        explanation = self._execute_skill("consumer_explainer", self.explainer_agent.run, explanation_payload)

        result = PipelineResult(
            trace_id=str(uuid.uuid4()),
            insight=insight,
            risk=risk,
            recommendation=recommendation,
            strategy_framework=strategy,
            explanation=explanation,
            cached=False,
            trace_log=self.registry.export_trace(),
            knowledge=knowledge_refs,
            workflow=applied_workflow,
        )
        self.cache.set(cache_key, result)
        return result
