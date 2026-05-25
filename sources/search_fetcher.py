"""Tavily 搜索补充模块。

用 Tavily API 搜索 10 个大厂官方域名，限定 site: 搜索。
"""

import logging

import requests

from config.settings import TAVILY_API_KEY, BIG_TECH_DOMAINS

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"
SEARCH_DOMAINS = [
    "openai.com", "anthropic.com", "google.com", "meta.com",
    "apple.com", "nvidia.com", "x.ai", "microsoft.com",
    "github.com", "aws.amazon.com",
]


def fetch() -> list:
    """搜索大厂官方域名，返回标准化事件列表。"""
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY 未设置，跳过搜索补充。")
        return []

    events = []
    for domain in SEARCH_DOMAINS:
        try:
            results = _search_domain(domain)
            for r in results:
                # 标准化
                title = (r.get("title") or "").strip()
                url = (r.get("url") or "").strip()
                content = (r.get("content") or "")[:260]
                published = (r.get("published_date") or "")

                if not title or not url:
                    continue

                events.append({
                    "title": title,
                    "summary": content[:260],
                    "source_name": domain.split(".")[0].capitalize(),
                    "source_url": url,
                    "event_type": "release",
                    "published_at": published,
                    "time_reason": "Tavily snippet" if published else "Tavily search",
                    "freshness": 12,
                    "official_score": 15,
                    "user_relevance": 13,
                    "product_value": 10,
                    "account_fit": 15,
                    "community_signal_score": 8,
                    "user_hook": "",
                    "overview": "",
                })
        except Exception as e:
            logger.warning("Tavily 搜索失败 [%s]: %s", domain, e)
            continue

    logger.info("Tavily 搜索到 %d 条事件", len(events))
    return events


def _search_domain(domain: str) -> list:
    """对单个域名发起 Tavily API 搜索。"""
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"site:{domain} AI",
        "search_depth": "basic",
        "max_results": 5,
        "include_domains": [domain],
    }
    resp = requests.post(TAVILY_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])
