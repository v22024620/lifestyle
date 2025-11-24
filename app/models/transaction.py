"""Transaction model."""
from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    studio_id: str
    amount: float
    currency: str = "KRW"
    status: str
    timestamp: str
