"""Helpers for pipeline scripts to load app Settings/.env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys
from typing import Tuple

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.config import Settings, get_settings


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Return shared Settings instance for standalone scripts."""
    return get_settings()


def neo4j_credentials() -> Tuple[str, str, str]:
    """Return (uri, user, password) ensuring password is configured."""
    settings = load_settings()
    if not settings.neo4j_password:
        raise RuntimeError(
            "LCP_NEO4J_PASSWORD is empty. Set it in .env before running this pipeline."
        )
    return settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
