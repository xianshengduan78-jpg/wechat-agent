"""候选池管理模块。

合并多个来源的事件，去重，健康度检查，自动触发搜索补充。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from config.settings import DATA_DIR, MIN_EVENTS, DIVERSITY_MIN_SOURCES
from sources import rss_fetcher, aihot_fetcher, search_fetcher

logger = logging.getLogger(__name__)

POOL_FILE = DATA_DIR / "topic-pool.json"


def refresh_pool() -> list:
    """刷新候选池：RSS + AIHOT + 搜索，去重后返回。

    如果合格事件数不够或来源不够，自动触发搜索补充。
    """
    logger.info("开始刷新候选池...")

    # 第一步：并行抓取三个来源
    rss_events = rss_fetcher.fetch_all()
    aihot_events = aihot_fetcher.fetch()
    search_events = search_fetcher.fetch()

    # 第二步：合并
    all_events = rss_events + aihot_events + search_events

    # 第三步：URL 去重
    seen_urls = set()
    unique_events = []
    for e in all_events:
        url = e.get("source_url", "").strip().rstrip("/")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        unique_events.append(e)

    # 第四步：健康度检查
    sources_count = _count_sources(unique_events)
    if len(unique_events) < MIN_EVENTS or sources_count < DIVERSITY_MIN_SOURCES:
        logger.info(
            "候选池事件数 %d (需≥%d), 来源数 %d (需≥%d)，触发搜索补充",
            len(unique_events), MIN_EVENTS, sources_count, DIVERSITY_MIN_SOURCES,
        )
        more = search_fetcher.fetch()
        for e in more:
            url = e.get("source_url", "").strip().rstrip("/")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_events.append(e)

    # 第五步：持久化
    _save_pool(unique_events)
    logger.info("候选池刷新完成: %d 条事件, %d 个来源",
                len(unique_events), _count_sources(unique_events))
    return unique_events


def load_pool() -> Optional[list]:
    """从本地加载缓存的候选池。"""
    if POOL_FILE.exists():
        try:
            with open(POOL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("候选池加载失败: %s", e)
    return None


def _save_pool(events: list) -> None:
    """持久化候选池到本地文件。"""
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "sources": _count_sources(events),
        "events": events,
    }
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(POOL_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.warning("候选池写入失败: %s", e)


def _count_sources(events: list) -> int:
    """统计事件列表中的来源数量。"""
    sources = set()
    for e in events:
        name = e.get("source_name", "")
        if name:
            sources.add(name)
    return len(sources)
