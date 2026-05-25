"""事件评分模块。

综合评分 = 眼球分×2 + 用户相关性×2 + 时效性 + 官方分 + 产品价值 + 账号匹配 + 社区热度
"""

from datetime import datetime, timezone, timedelta

from config.settings import PRIMARY_WINDOW_HOURS

# 高/低表现事件类型（后续由策略记忆动态更新）
HIGH_PERF_TYPES = {"release", "product", "open_source", "price", "agent"}
LOW_PERF_TYPES = {"policy", "safety_report", "regulation"}

# 眼球关键词
EYE_KEYWORDS = [
    "免费", "降价", "开放", "Agent", "图片", "视频",
    "开源", "发布", "新模型", "GPT", "Claude", "Gemini",
    "打败", "超过", "首次", "震撼", "惊人",
]


def score_event(event: dict) -> dict:
    """对单条事件计算综合评分，原地修改并返回。"""
    # 1. 眼球分（0-20）
    eye_score = _calc_eye_score(event)

    # 2. 时效性（0-20）
    freshness = event.get("freshness", 10)

    # 3. 用户相关性（0-20）
    user_relevance = event.get("user_relevance", 10)

    # 4. 官方分（0-20）
    official_score = event.get("official_score", 10)

    # 5. 产品价值（0-20）
    product_value = event.get("product_value", 10)

    # 6. 账号匹配（0-20）
    account_fit = event.get("account_fit", 10)

    # 7. 社区热度（0-20）
    community_signal = event.get("community_signal_score", 5)

    # 综合评分
    total = (
        eye_score * 2
        + user_relevance * 2
        + freshness
        + official_score
        + product_value
        + account_fit
        + community_signal
    )

    # 事件类型加成/减成
    etype = event.get("event_type", "")
    if etype in HIGH_PERF_TYPES:
        total += 5
    elif etype in LOW_PERF_TYPES:
        total -= 8

    # 时效性衰减：超过主窗口的降权
    pub_at = event.get("published_at", "")
    if pub_at:
        try:
            dt = datetime.fromisoformat(pub_at)
            now = datetime.now(timezone.utc)
            hours_ago = (now - dt).total_seconds() / 3600
            if hours_ago > PRIMARY_WINDOW_HOURS:
                total *= 0.7  # 超过 24h 打 7 折
        except (ValueError, TypeError):
            pass

    event["eye_score"] = eye_score
    event["total_score"] = round(total, 1)
    return event


def _calc_eye_score(event: dict) -> int:
    """计算眼球分：匹配关键词越多越高。"""
    text = f"{event.get('title', '')} {event.get('summary', '')} {event.get('user_hook', '')}"
    lower = text.lower()
    matches = sum(1 for kw in EYE_KEYWORDS if kw.lower() in lower)
    # 最多 20 分
    return min(matches * 4, 20)
