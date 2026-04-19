#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
题材映射（hszg/zg）：
- 单股题材查询
- 代码归一化（sz000001/sh600519 -> 000001）
- 落盘缓存（跨天复用）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from ..cache.json_cache import read_json, write_json
from ..config import AppConfig, DEFAULT_CONFIG
from ..http import HttpClient
from .clean import clean_theme


def normalize_stock_code(dm: str) -> str:
    if not dm:
        return ""
    digits = "".join([c for c in str(dm) if c.isdigit()])
    return digits[-6:] if len(digits) >= 6 else digits


@dataclass
class ThemeMapper:
    client: HttpClient
    cache_path: Path
    cfg: AppConfig = DEFAULT_CONFIG
    timeout: int = 5

    def load_cache(self) -> Dict[str, List[str]]:
        raw = read_json(self.cache_path)
        codes = raw.get("codes", {}) if isinstance(raw, dict) else {}
        if not isinstance(codes, dict):
            return {}
        # 简单净化：确保 list[str]
        cleaned = {}
        for k, v in codes.items():
            if isinstance(v, list):
                cleaned[k] = [t for t in v if t and t not in self.cfg.exclude_theme_names and t not in self.cfg.noise_themes]
            else:
                cleaned[k] = []
        return cleaned

    def save_cache(self, codes: Dict[str, List[str]]) -> None:
        write_json(self.cache_path, {"version": 1, "codes": codes})

    def fetch_stock_themes(self, code6: str, codes_cache: Dict[str, List[str]]) -> List[str]:
        if not code6:
            return []
        if code6 in codes_cache:
            return codes_cache[code6]

        url = f"{self.client.base_url}/hszg/zg/{code6}/{self.client.token}"
        data = self.client.get_json(url)
        result: list[str] = []
        if isinstance(data, list):
            for item in data:
                t = clean_theme(item.get("name", ""), self.cfg)
                if t and t not in self.cfg.noise_themes:
                    result.append(t)

        # 去重保序
        seen = set()
        uniq = []
        for t in result:
            if t in seen:
                continue
            seen.add(t)
            uniq.append(t)

        codes_cache[code6] = uniq
        return uniq

