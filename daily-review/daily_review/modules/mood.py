#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
情绪模块（v1 registry 兼容）：基于 features.mood_inputs 重建 mood/moodStage/moodCards
"""

from __future__ import annotations

from typing import Any, Dict

from daily_review.metrics.mood import rebuild_mood


def rebuild_mood_panel(market_data: Dict[str, Any]) -> Dict[str, Any]:
    features = market_data.get("features") or {}
    inputs = features.get("mood_inputs") or {}
    patch = rebuild_mood(inputs)
    return patch

