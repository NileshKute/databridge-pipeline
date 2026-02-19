from __future__ import annotations

import os
from pathlib import Path

from backend.app.core.config import settings


def validate_staging_path(path: str) -> bool:
    resolved = os.path.realpath(path)
    return resolved.startswith(os.path.realpath(settings.STAGING_NETWORK_PATH))


def validate_production_path(path: str) -> bool:
    resolved = os.path.realpath(path)
    return resolved.startswith(os.path.realpath(settings.PRODUCTION_NETWORK_PATH))


def get_directory_size(path: str) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def human_readable_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


def ensure_directory(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
