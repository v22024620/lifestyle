from __future__ import annotations
"""Pipeline orchestrator wiring all agents and services."""
import csv
import uuid
from typing import Any, Dict, List

from app.config import Settings
from app.services.graphrag_service import GraphRAGService
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.services.neo4j_service import Neo4jService
from app.utils.llm_client import LLMClient
from app.utils.cache import TTLCache
from app.models.pipeline import PipelineResult
from app.agents.wellness_insight_agent import WellnessInsightAgent
from app.agents.risk_guard_agent import RiskGuardAgent
from app.agents.revenue_architect_agent import RevenueArchitectAgent
from app.agents.strategy_framework_agent import StrategyFrameworkAgent
from app.agents.consumer_explainer_agent import ConsumerExplainerAgent


class AgentOrchestrator:
    """Run full multi-agent pipeline and aggregate outputs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMClient(settings.llm_endpoint, api_key=settings.openai_api_key)
        self.vector = VectorService(settings.chroma_path)
        self.ontology = OntologyService(settings.graphdb_endpoint)
        self.neo4j = Neo4jService(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        self.graphrag = GraphRAGService(self.vector, self.ontology, self.neo4j)
        self.insight_agent = WellnessInsightAgent(self.llm)
        self.risk_agent = RiskGuardAgent(self.llm)
        self.reco_agent = RevenueArchitectAgent(self.llm)
        self.strategy_agent = StrategyFrameworkAgent(self.llm)
        self.explainer_agent = ConsumerExplainerAgent(self.llm)
        self.cache = TTLCache(ttl_seconds=self.settings.cache_ttl_seconds, max_size=5)
        self._bootstrap_vector_samples()
        self.graphrag.seed_neo4j_from_ontology()

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

    def run_full_pipeline(self, user_query: str | None, studio_id: str) -> PipelineResult:
        """Execute pipeline and return aggregated dataclass. Uses TTL cache."""
        cache_key = (studio_id, user_query or "")
        cached: PipelineResult | None = self.cache.get(cache_key)
        if cached:
            refreshed = cached.refresh(mark_cached=True)
            self.cache.set(cache_key, cached)
            return refreshed

        trace_id = str(uuid.uuid4())
        context = self.graphrag.build_context(user_query, studio_id)
        insight = self.insight_agent.run(context)
        risk = self.risk_agent.run(context)
        recommendation = self.reco_agent.run(context)
        strategy = self.strategy_agent.run({**context, "insight": insight, "risk": risk, "recommendation": recommendation})
        explanation = self.explainer_agent.run({"insight": insight, "risk": risk, "recommendation": recommendation, "strategy": strategy})
        result = PipelineResult(
            trace_id=trace_id,
            insight=insight,
            risk=risk,
            recommendation=recommendation,
            strategy_framework=strategy,
            explanation=explanation,
            cached=False,
        )
        self.cache.set(cache_key, result)
        return result
