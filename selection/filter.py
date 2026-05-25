"""事件排除规则模块。

按预定义规则排除不合格事件，返回排除原因。
"""

from datetime import datetime, timezone

from config.settings import (
    SECONDARY_WINDOW_HOURS,
    MIN_USER_RELEVANCE,
    MIN_COMMUNITY_SIGNAL,
)

# 政策/军方噪音关键词
NOISE_KEYWORDS = [
    "regulation", "compliance", "executive order", "military",
    "国防", "军事", "监管", "合规", "政策", "法案",
]


def exclude_events(events: list) -> tuple:
    """对事件列表执行排除规则，返回 (合格列表, 排除报告列表)。

    排除报告: [(event_title, reason), ...]
    """
    keep = []
    excluded = []

    for event in events:
        reason = _check_exclusion(event)
        if reason:
            excluded.append((event.get("title", ""), reason))
        else:
            keep.append(event)

    return keep, excluded


def _check_exclusion(event: dict) -> str:
    """检查单条事件是否需要排除，返回排除原因或空字符串。"""
    title = event.get("title", "")

    # 1. 无可靠时间 → 排除
    pub_at = event.get("published_at", "")
    if not pub_at:
        return "无可靠时间"

    # 2. 超过时间窗口 → 排除
    try:
        dt = datetime.fromisoformat(pub_at)
        now = datetime.now(timezone.utc)
        hours_ago = (now - dt).total_seconds() / 3600
        if hours_ago > SECONDARY_WINDOW_HOURS:
            return f"超过 {SECONDARY_WINDOW_HOURS}h 窗口"
    except (ValueError, TypeError):
        return "时间格式异常"

    # 3. 政策/军方噪音 → 排除
    combined = f"{title} {event.get('summary', '')}".lower()
    if any(kw.lower() in combined for kw in NOISE_KEYWORDS):
        return "政策/军方噪音"

    # 4. 用户关注度 < 12 → 排除
    if event.get("user_relevance", 0) < MIN_USER_RELEVANCE:
        return f"用户关注度 {event.get('user_relevance')} < {MIN_USER_RELEVANCE}"

    # 5. 社区热度 < 8 → 排除
    if event.get("community_signal_score", 0) < MIN_COMMUNITY_SIGNAL:
        return f"社区热度 {event.get('community_signal_score')} < {MIN_COMMUNITY_SIGNAL}"

    return ""
