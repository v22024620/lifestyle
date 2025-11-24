"""Studio model."""
from pydantic import BaseModel


class Studio(BaseModel):
    id: str
    name: str
    modality: str | None = None
    region: str | None = None
