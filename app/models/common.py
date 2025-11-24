"""Common shared pydantic models."""
from pydantic import BaseModel


class Traceable(BaseModel):
    trace_id: str | None = None
