"""微信后台数据拉取模块。

调微信 datacube 接口获取文章表现数据（阅读数、分享数、收藏数等）。
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from config.settings import (
    DATA_DIR, DATACUBE_URL, DATACUBE_GETARTICLESUM_URL,
    FREEPUBLISH_BATCHGET_URL,
)

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
    """通过 getarticlesummary 获取最近文章数据（按日期范围）。

    注意：此 API 仅对认证服务号/认证订阅号开放。
    个人订阅号调用会返回 48001（无权限）。
    """
    logger.info("通过 getarticlesummary 拉取文章数据...")
    articles = []
    today = datetime.now(timezone.utc)

    try:
        resp = requests.post(
            DATACUBE_GETARTICLESUM_URL,
            params={"access_token": access_token},
            json={
                "begin_date": (today - timedelta(days=days)).strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "list" in data:
            seen_titles = set()
            for item in data["list"]:
                title = item.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    articles.append({
                        "title": title,
                        "article_id": item.get("articleid", item.get("ref_date", "")),
                        "ref_date": item.get("ref_date", ""),
                    })
            logger.info("getarticlesummary 获取到 %d 篇文章", len(articles))
        else:
            errcode = data.get("errcode")
            if errcode == 48001:
                logger.warning("数据统计 API 无权限（需要认证订阅号/服务号），当前账号可能为个人订阅号")
            else:
                logger.warning("getarticlesummary 返回异常: %s", data)

        return articles

    except Exception as e:
        logger.warning("getarticlesummary 调用失败: %s", e)
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
