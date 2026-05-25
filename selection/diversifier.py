"""来源多样性控制模块。

确保入选事件来自多个不同来源，单一来源不超过上限。
"""

import logging
from collections import Counter

from config.settings import SINGLE_SOURCE_MAX, DIVERSITY_MIN_SOURCES

logger = logging.getLogger(__name__)


def diversify(events: list, scores: dict = None) -> list:
    """按来源多样性调整事件列表。

    规则：
    1. 单源上限（默认 4 条/源）
    2. 来源多样性最低要求（至少 3 个不同来源）

    如果多样性不足，会发出警告但不会硬性移除事件
    （selector 上层决定是否补选）。
    """
    if not events:
        return events

    # 统计来源
    source_count: Counter = Counter()
    result = []

    for e in events:
        source = e.get("source_name", "unknown")
        if source_count[source] < SINGLE_SOURCE_MAX:
            source_count[source] += 1
            result.append(e)
        else:
            logger.debug("来源 [%s] 已达上限 %d 条，移除: %s",
                         source, SINGLE_SOURCE_MAX, e.get("title", ""))

    actual_sources = len(source_count)
    if actual_sources < DIVERSITY_MIN_SOURCES:
        logger.warning(
            "来源多样性不足: 当前 %d 个来源，需要至少 %d 个",
            actual_sources, DIVERSITY_MIN_SOURCES,
        )

    return result
