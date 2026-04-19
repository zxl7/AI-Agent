#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块注册表：用于“部分更新”（只更新某个模块）
"""

from __future__ import annotations

from typing import Callable, Dict, Any

from .style_radar import rebuild_style_radar
from .mood import rebuild_mood_panel

ModuleFn = Callable[[Dict[str, Any]], Dict[str, Any]]


REGISTRY: dict[str, ModuleFn] = {
    "style_radar": rebuild_style_radar,
    "mood": rebuild_mood_panel,
}


def available_modules() -> list[str]:
    return sorted(REGISTRY.keys())


def apply_modules(market_data: Dict[str, Any], modules: list[str]) -> Dict[str, Any]:
    """
    返回更新后的 market_data（原地更新并返回引用，方便调用者）。
    """
    for name in modules:
        fn = REGISTRY.get(name)
        if not fn:
            raise KeyError(f"未知模块: {name}，可选：{', '.join(available_modules())}")
        patch = fn(market_data)
        # patch 必须返回 dict，且只包含需要覆盖的 key
        for k, v in patch.items():
            market_data[k] = v
    return market_data
