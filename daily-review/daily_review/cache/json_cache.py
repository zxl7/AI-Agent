#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON 缓存通用工具
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def read_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def prune_days(map_by_day: Dict[str, Any], keep_days: list[str]) -> Dict[str, Any]:
    keep = set(keep_days or [])
    return {d: v for d, v in (map_by_day or {}).items() if d in keep}

