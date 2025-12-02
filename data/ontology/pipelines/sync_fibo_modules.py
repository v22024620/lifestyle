"""Sync selected FIBO modules from fibo-master into data/ontology/raw."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[3]))

from data.ontology.pipelines.config_loader import (  # type: ignore  # pylint:disable=import-error
    ConfigError,
    ONTOLOGY_ROOT,
    REPO_ROOT,
    SyncModule,
    load_sync_modules,
)

FIBO_DIR_NAME = "fibo-master"


def ensure_fibo_root() -> Path:
    fibo_root = (REPO_ROOT / FIBO_DIR_NAME).resolve()
    if not fibo_root.exists():
        raise ConfigError(
            f"Missing {fibo_root}. Clone edmcouncil/fibo or download release as '{FIBO_DIR_NAME}'."
        )
    return fibo_root


def copy_path(src: Path, dest: Path, *, clean: bool, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY-RUN] Would sync {src} -> {dest}")
        return
    if clean and dest.exists():
        if dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    print(f"[SYNC] {src} -> {dest}")


def resolve_destination(module: SyncModule, rel_path: str) -> Path:
    target_root = (ONTOLOGY_ROOT / module.target).resolve()
    if not str(target_root).startswith(str(ONTOLOGY_ROOT)):
        raise ConfigError(f"Invalid target {target_root}")
    relative = Path(rel_path)
    return target_root / relative.name if relative.is_file() else target_root / relative


def sync_module(module: SyncModule, fibo_root: Path, *, clean: bool, dry_run: bool) -> None:
    module_root = (fibo_root / module.source).resolve()
    for rel in module.paths:
        src = (module_root / rel).resolve()
        if not src.exists():
            print(f"[WARN] Missing source {src} for module {module.name}")
            continue
        dest = resolve_destination(module, rel)
        copy_path(src, dest, clean=clean, dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Bloomberg FIBO modules into ontology/raw")
    parser.add_argument("--module", action="append", dest="modules", help="Only sync specific module names")
    parser.add_argument("--clean", action="store_true", help="Remove target directories before copying")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without copying")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    modules = load_sync_modules()
    selected = [m for m in modules if not args.modules or m.name in args.modules]
    if not selected:
        print("[INFO] No modules selected (check --module names)")
        return
    fibo_root = ensure_fibo_root()
    for module in selected:
        print(f"[INFO] Syncing {module.name}: {module.description}")
        sync_module(module, fibo_root, clean=args.clean, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except ConfigError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


