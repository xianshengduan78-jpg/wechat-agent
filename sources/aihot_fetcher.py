"""AIHOT API 聚合抓取模块。

从 AIHOT API (https://aihot.virxact.com/api/public/items) 抓取过去 24h 精选。
"""

import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

AIHOT_API_URLS = [
    "https://aihot.virxact.com/api/public/items",
    "https://aihot.cc/api/public/items",
]


def fetch() -> list:
    """抓取 AIHOT 过去 24h 精选事件，返回标准化列表。"""
    events = []
    data = None
    for url in AIHOT_API_URLS:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                break
        except Exception:
            continue
    else:
        logger.warning("AIHOT API 所有端点均不可用")
        return events

    now = datetime.now(timezone.utc)

    for item in data.get("data", data if isinstance(data, list) else []):
        if isinstance(item, dict):
            events.append(_to_event(item, now))
        else:
            continue

    logger.info("AIHOT 抓取到 %d 条事件", len(events))
    return events


def _to_event(item: dict, now: datetime) -> dict:
    """将 AIHOT API 返回格式转为标准化事件格式。"""
    title = (item.get("title") or "").strip()
    summary = (item.get("description") or item.get("summary") or item.get("content") or "")[:260]
    source_url = item.get("url") or item.get("link") or item.get("source_url") or ""
    source_name = item.get("source") or item.get("source_name") or "AIHOT"

    published_at = item.get("published_at") or item.get("created_at") or ""
    time_reason = "AIHOT API timestamp"

    return {
        "title": title,
        "summary": summary,
        "source_name": source_name,
        "source_url": source_url,
        "event_type": "release",
        "published_at": published_at,
        "time_reason": time_reason,
        "freshness": 15,
        "official_score": 10,
        "user_relevance": 15,
        "product_value": 10,
        "account_fit": 10,
        "community_signal_score": 15,
        "user_hook": "",
        "overview": "",
    }
