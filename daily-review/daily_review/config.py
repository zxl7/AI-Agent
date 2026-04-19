#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置层（数据源 / 过滤口径 / 权重阈值）

原则：
- 所有“口径”与“常量”集中在这里，避免散落在各模块导致难以维护。
- 允许后续把 token 等敏感信息迁移到环境变量或单独的本地配置文件。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    base_url: str = "https://api.biyingapi.com"
    token: str = "60D084A7-FF4A-4B42-9E1C-45F0B719F33C"

    # 题材清洗口径
    noise_prefixes: tuple[str, ...] = (
        "A股-分类",
        "A股-指数成分",
        "A股-证监会行业",
        "A股-申万行业",
        "A股-申万二级",
        "A股-地域板块",
        "基金-",
        "港股-",
        "美股-",
        "A股-概念板块",
    )
    noise_themes: set[str] = frozenset(
        {
            "小盘",
            "中盘",
            "大盘",
            "融资融券",
            "QFII持股",
            "基金重仓",
            "年度强势",
            "深股通",
            "沪股通",
            "富时罗素",
        }
    )
    exclude_theme_names: set[str] = frozenset({"昨日涨停", "昨日连板"})


DEFAULT_CONFIG = AppConfig()

