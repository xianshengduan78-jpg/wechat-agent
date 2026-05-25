"""策略记忆模块。

记录选题偏好、标题策略、封面策略、写作备注。
手动编辑 data/strategy-memory.json 即可调整。
"""

import json
import logging
from copy import deepcopy

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
}


def load() -> dict:
    """加载策略记忆，不存在时返回默认值。"""
    if not STRATEGY_FILE.exists():
        return deepcopy(DEFAULT_STRATEGY)
    try:
        with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
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
