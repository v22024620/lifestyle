"""FastAPI application entrypoint."""
from fastapi import FastAPI

from app.api.router import api_router
from app.utils.logging import configure_logging


configure_logging()
app = FastAPI(title="LOP - Lifestyle Ontology Partner")
app.include_router(api_router)


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
