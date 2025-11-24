"""Simulation endpoints for fee plans."""
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.services.recommendation_simulator import RecommendationSimulator
from app.config import get_settings


class Period(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = ConfigDict(populate_by_name=True)


class FeePlanSimulationRequest(BaseModel):
    studio_id: str
    current_plan: str
    candidate_plans: list[str]
    period: Period

    model_config = ConfigDict(populate_by_name=True)


router = APIRouter()
simulator = RecommendationSimulator(settings=get_settings())


@router.post("/fee-plan")
def simulate_fee_plan(payload: FeePlanSimulationRequest) -> dict:
    """Mock fee plan simulation using revenue architect agent output."""
    return simulator.simulate(payload)
