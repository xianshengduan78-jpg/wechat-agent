"""AIHOT API 聚合抓取模块。

从 https://aihot.virxact.com/api/public/items 抓取过去 72h 精选事件。
API 匿名免费，无需 token。
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

logger = logging.getLogger(__name__)

AIHOT_API_BASE = "https://aihot.virxact.com/api/public/items"

BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch(hours: int = 72) -> list:
    """抓取 AIHOT 精选事件，返回标准化列表。"""
    events = []
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        resp = requests.get(
            AIHOT_API_BASE,
            params={"mode": "selected", "since": since},
            headers={"User-Agent": BROWSER_UA},
            timeout=15,
        )
        if resp.status_code == 403:
            logger.warning("AIHOT API 返回 403，可能被限流")
            return events
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("AIHOT API 抓取失败: %s", e)
        return events

    items = data.get("items", [])
    if not items:
        logger.info("AIHOT 无事件")
        return events

    for item in items:
        if isinstance(item, dict):
            events.append(_to_event(item))

    logger.info("AIHOT 抓取到 %d 条事件", len(events))
    return events


def _to_event(item: dict) -> dict:
    """将 AIHOT API 返回格式转为标准化事件格式。"""
    title = (item.get("title") or "").strip()
    summary = (item.get("summary") or "")[:260]
    source_url = (item.get("url") or "").strip()
    source_name = item.get("source") or "AIHOT"
    published_at = (item.get("publishedAt") or "").strip()
    category = item.get("category", "release")

    # 事件类型映射
    event_type = _map_category(category)

    return {
        "title": title,
        "summary": summary,
        "source_name": source_name,
        "source_url": source_url,
        "event_type": event_type,
        "published_at": published_at,
        "time_reason": "AIHOT API timestamp",
        "freshness": 15,
        "official_score": 8,
        "user_relevance": 16,
        "product_value": 12,
        "account_fit": 12,
        "community_signal_score": 16,
        "user_hook": "",
        "overview": "",
    }


def _map_category(category: str) -> str:
    """将 AIHOT category 映射到内部事件类型。"""
    mapping = {
        "model": "release",
        "product": "product",
        "industry": "release",
        "paper": "research",
        "tips": "product",
    }
    return mapping.get(category, "release")
