"""Shared configuration helpers for ontology pipelines."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

import yaml

PIPELINES_DIR = Path(__file__).resolve().parent
ONTOLOGY_ROOT = PIPELINES_DIR.parent
REPO_ROOT = PIPELINES_DIR.parents[2]
GRAPHDB_CONFIG_PATH = PIPELINES_DIR / "graphdb_modules.yml"
MODULES_CONFIG_PATH = PIPELINES_DIR / "modules.json"


class ConfigError(RuntimeError):
    """Raised when a configuration file is missing or malformed."""


@dataclass(frozen=True)
class Layer:
    name: str
    description: str
    files: List[str]
    optional: bool = False

    def iter_files(self) -> Iterator[str]:
        yield from self.files


@dataclass(frozen=True)
class SyncModule:
    name: str
    source: str
    target: str
    paths: List[str]
    description: str


def _require(path: Path) -> str:
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")
    return path.read_text(encoding='utf-8-sig')


def load_graphdb_layers(config_path: Optional[Path] = None) -> List[Layer]:
    path = config_path or GRAPHDB_CONFIG_PATH
    data = yaml.safe_load(_require(path)) or {}
    layers = data.get("layers")
    if not layers:
        raise ConfigError(f"No 'layers' entries in {path}")
    seen: set[str] = set()
    results: List[Layer] = []
    for raw in layers:
        name = raw.get("name")
        files = raw.get("files") or []
        if not name or not files:
            raise ConfigError(f"Invalid layer in {path}: {raw}")
        if name in seen:
            raise ConfigError(f"Duplicate layer '{name}'")
        seen.add(name)
        results.append(
            Layer(
                name=name,
                description=raw.get("description", ""),
                files=[str(f) for f in files],
                optional=bool(raw.get("optional", False)),
            )
        )
    return results


def iter_layer_files(
    *,
    include_optional: bool = True,
    only_layers: Optional[Iterable[str]] = None,
    config_path: Optional[Path] = None,
) -> Iterator[str]:
    selected = {name for name in only_layers} if only_layers else None
    for layer in load_graphdb_layers(config_path):
        if selected and layer.name not in selected:
            continue
        if layer.optional and not include_optional:
            continue
        yield from layer.iter_files()


def resolve_ontology_path(relative_path: str) -> Path:
    candidate = (ONTOLOGY_ROOT / relative_path).resolve()
    if not str(candidate).startswith(str(ONTOLOGY_ROOT)):
        raise ConfigError(f"Path escapes ontology root: {relative_path}")
    return candidate


def load_sync_modules(config_path: Optional[Path] = None) -> List[SyncModule]:
    path = config_path or MODULES_CONFIG_PATH
    data = json.loads(_require(path))
    modules = data.get("modules") or []
    results: List[SyncModule] = []
    for raw in modules:
        name = raw.get("name")
        source = raw.get("source")
        target = raw.get("target")
        paths = raw.get("paths") or []
        if not name or not source or not target or not paths:
            raise ConfigError(f"Invalid module entry: {raw}")
        results.append(
            SyncModule(
                name=name,
                source=str(source),
                target=str(target),
                paths=[str(p) for p in paths],
                description=str(raw.get("description", "")),
            )
        )
    if not results:
        raise ConfigError(f"No modules declared in {path}")
    return results


__all__ = [
    "ConfigError",
    "GRAPHDB_CONFIG_PATH",
    "MODULES_CONFIG_PATH",
    "ONTOLOGY_ROOT",
    "PIPELINES_DIR",
    "REPO_ROOT",
    "Layer",
    "SyncModule",
    "iter_layer_files",
    "load_graphdb_layers",
    "load_sync_modules",
    "resolve_ontology_path",
]
