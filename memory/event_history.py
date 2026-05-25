"""已发事件历史管理（用于去重和表现分析）。"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

HISTORY_FILE = DATA_DIR / "daily-event-history.json"


def load() -> list:
    """加载历史事件列表。"""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("历史文件加载失败: %s", e)
        return []


def append(new_events: list) -> None:
    """追加新事件到历史。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = load()
    history.extend(new_events)
    _save(history)
    logger.info("历史追加 %d 条事件，总计 %d 条", len(new_events), len(history))


def get_titles() -> list:
    """获取历史事件标题列表。"""
    return [e.get("title", "") for e in load() if isinstance(e, dict)]


def deduplicate(events: list) -> list:
    """对比历史，返回不在历史中的事件。"""
    history_titles = set(get_titles())
    return [e for e in events if e.get("title", "") not in history_titles]


def clear() -> None:
    """清空历史（用于调试）。"""
    _save([])
    logger.info("历史已清空")


def _save(history: list) -> None:
    """持久化历史。"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.warning("历史文件写入失败: %s", e)
