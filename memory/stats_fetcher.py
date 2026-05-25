"""微信后台数据拉取模块。

调微信 datacube 接口获取文章表现数据（阅读数、分享数、收藏数等）。
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR, DATACUBE_URL

logger = logging.getLogger(__name__)

PERF_FILE = DATA_DIR / "performance-history.json"


def fetch_article_total(access_token: str, article_id: str) -> Optional[dict]:
    """拉取单篇文章的阅读数据。"""
    today = datetime.now(timezone.utc)
    body = {
        "begin_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": today.strftime("%Y-%m-%d"),
        "article_id": article_id,
    }
    try:
        resp = requests.post(
            DATACUBE_URL,
            params={"access_token": access_token},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "list" in data:
            return _aggregate_stats(data["list"])
        else:
            logger.warning("数据拉取返回异常: %s", data)
            return None
    except Exception as e:
        logger.error("数据拉取失败: %s", e)
        return None


def fetch_recent_articles(access_token: str, days: int = 7) -> list:
    """拉取最近 N 天已发布文章列表（通过草稿/发布接口）。

    注意：微信 datacube getarticletotal 需要 article_id，
    这里需要先从发布列表获取 article_id。
    """
    # 微信 datacube 接口不直接返回文章列表
    # 需要先通过素材管理接口获取已发布文章
    # 此功能依赖微信"发布能力"接口
    logger.info("拉取最近 %d 天文章数据...", days)
    # 实际使用时需要结合 getarticle 接口
    return []


def save_performance(performance: dict) -> None:
    """持久化表现数据。"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 追加到历史
        if PERF_FILE.exists():
            with open(PERF_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        if not isinstance(history, list):
            history = []
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": performance,
        })
        with open(PERF_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info("表现数据已保存")
    except OSError as e:
        logger.warning("表现数据写入失败: %s", e)


def _aggregate_stats(raw_list: list) -> dict:
    """聚合原始数据，按事件类型归类。"""
    aggregated = {}
    for item in raw_list:
        title = item.get("title", "")
        details = item.get("details", [])
        total_reads = sum(d.get("read_count", 0) for d in details)
        total_shares = sum(d.get("share_count", 0) for d in details)
        total_likes = sum(d.get("like_count", 0) for d in details)
        total_collect = sum(d.get("collect_count", 0) for d in details)
        total_impressions = sum(d.get("int_page_read_count", 0) + d.get("ori_page_read_count", 0) for d in details)

        read_rate = round(total_reads / total_impressions, 4) if total_impressions > 0 else 0

        aggregated[title] = {
            "impressions": total_impressions,
            "reads": total_reads,
            "shares": total_shares,
            "likes": total_likes,
            "collects": total_collect,
            "read_rate": read_rate,
        }

    return aggregated
