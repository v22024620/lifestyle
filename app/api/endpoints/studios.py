"""Studio insight endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_orchestrator import AgentOrchestrator
from app.config import get_settings


class InsightRequest(BaseModel):
    query: str | None = None


router = APIRouter()
settings = get_settings()
orchestrator = AgentOrchestrator(settings=settings)


@router.post("/{studio_id}/insights")
def studio_insights(studio_id: str, payload: InsightRequest) -> dict:
    """Return aggregated insights for a wellness studio using the agent pipeline."""
    result = orchestrator.run_full_pipeline(user_query=payload.query, studio_id=studio_id)
    return result.to_dict()
