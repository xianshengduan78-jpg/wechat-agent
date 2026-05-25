"""策略记忆模块。

记录选题偏好、标题策略、封面策略、写作备注。
数据驱动更新：根据历史表现调整后续策略。
"""

import json
import logging
from copy import deepcopy
from typing import Optional

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

STRATEGY_FILE = DATA_DIR / "strategy-memory.json"

DEFAULT_STRATEGY = {
    "high_perf_types": ["release", "product", "open_source", "price", "agent"],
    "low_perf_types": ["policy", "safety_report", "regulation"],
    "recommended_event_count": 12,
    "title_strategy": "信息型为主，反差型为辅",
    "cover_strategy": "用最有代表性的事件截图 + 短钩子主标题",
    "writing_notes": "",
    "title_type_performance": {},
    "event_type_performance": {},
}


def load() -> dict:
    """加载策略记忆，不存在时返回默认值。"""
    if not STRATEGY_FILE.exists():
        return deepcopy(DEFAULT_STRATEGY)
    try:
        with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 合入默认值（防止新增字段缺失）
        merged = deepcopy(DEFAULT_STRATEGY)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("策略记忆加载失败: %s", e)
        return deepcopy(DEFAULT_STRATEGY)


def save(strategy: dict) -> None:
    """持久化策略记忆。"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
            json.dump(strategy, f, ensure_ascii=False, indent=2)
        logger.info("策略记忆已保存")
    except OSError as e:
        logger.warning("策略记忆写入失败: %s", e)


def update_from_performance(performance: dict) -> dict:
    """根据表现数据更新策略记忆。

    Args:
        performance: {event_type: {impressions, reads, shares, likes, ...}}

    Returns:
        更新后的策略记忆
    """
    strategy = load()

    if not performance:
        return strategy

    # 按事件类型分组分析阅读表现
    type_perf = {}
    for etype, stats in performance.items():
        read_rate = stats.get("read_rate", 0)
        type_perf[etype] = read_rate

    strategy["event_type_performance"] = type_perf

    # 找出高/低表现类型
    if type_perf:
        sorted_types = sorted(type_perf.items(), key=lambda x: x[1], reverse=True)
        mid = len(sorted_types) // 2
        strategy["high_perf_types"] = [t for t, _ in sorted_types[:mid]]
        strategy["low_perf_types"] = [t for t, _ in sorted_types[mid:]]

    save(strategy)
    logger.info("策略已根据表现数据更新")
    return strategy
