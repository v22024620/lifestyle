"""Minimal settings helper for pipeline scripts."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('.env'), override=False)


def _env(key: str, fallback_keys: tuple[str, ...] | None = None) -> str:
    keys = (key,) + tuple(fallback_keys or ())
    for candidate in keys:
        value = os.environ.get(candidate)
        if value:
            return value
    raise RuntimeError(f"Environment variable {key} is required for this pipeline")


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str


def neo4j_credentials() -> tuple[str, str, str]:
    settings = Neo4jSettings(
        uri=_env("LCP_NEO4J_URI", ("NEO4J_URI",)),
        user=_env("LCP_NEO4J_USERNAME", ("LCP_NEO4J_USER", "NEO4J_USERNAME", "NEO4J_USER")),
        password=_env("LCP_NEO4J_PASSWORD", ("NEO4J_PASSWORD",)),
    )
    return settings.uri, settings.user, settings.password
