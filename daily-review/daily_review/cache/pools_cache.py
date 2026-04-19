#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
池子缓存（涨停/跌停/炸板）：
- 7 日落盘缓存
- 预热（首次补齐）
- 缓存裁剪
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ..http import HttpClient
from .json_cache import read_json, write_json, prune_days


@dataclass
class PoolsCache:
    client: HttpClient
    cache_path: Path
    version: int = 1

    def load(self) -> Dict[str, Any]:
        cache = read_json(self.cache_path)
        if cache.get("version") != self.version:
            return {"version": self.version, "pools": {"ztgc": {}, "dtgc": {}, "zbgc": {}}}
        pools = cache.get("pools") or {}
        return {
            "version": self.version,
            "pools": {
                "ztgc": pools.get("ztgc") or {},
                "dtgc": pools.get("dtgc") or {},
                "zbgc": pools.get("zbgc") or {},
            },
        }

    def save(self, cache: Dict[str, Any]) -> None:
        cache["version"] = self.version
        write_json(self.cache_path, cache)

    def fetch(
        self,
        cache: Dict[str, Any],
        pool_name: str,
        date_str: str,
        *,
        use_cache_first: bool,
    ) -> List[Dict[str, Any]]:
        pools = cache["pools"]
        pool_cache = pools.get(pool_name) or {}

        if use_cache_first and date_str in pool_cache:
            return pool_cache.get(date_str) or []

        data = self.client.api(f"hslt/{pool_name}/{date_str}", exit_on_404=False, quiet_404=True) or []
        pool_cache[date_str] = data
        pools[pool_name] = pool_cache
        return data

    def warmup_and_prune(self, cache: Dict[str, Any], keep_days: List[str]) -> Dict[str, Any]:
        """
        对历史日预热缓存，并裁剪只保留 keep_days。
        """
        for d in keep_days:
            # warmup 只负责“确保缓存存在”，因此优先缓存
            self.fetch(cache, "ztgc", d, use_cache_first=True)
            self.fetch(cache, "dtgc", d, use_cache_first=True)
            self.fetch(cache, "zbgc", d, use_cache_first=True)

        cache["pools"]["ztgc"] = prune_days(cache["pools"]["ztgc"], keep_days)
        cache["pools"]["dtgc"] = prune_days(cache["pools"]["dtgc"], keep_days)
        cache["pools"]["zbgc"] = prune_days(cache["pools"]["zbgc"], keep_days)
        return cache

