"""RSS 源抓取模块。

从 15 个官方 feed 抓取 AI 相关新闻，返回标准化事件列表。
"""

import logging
from datetime import datetime, timezone, timedelta

import feedparser
import requests

from config.settings import FEEDS, SECONDARY_WINDOW_HOURS

logger = logging.getLogger(__name__)

# 用于过滤非 AI 相关关键词
AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "deep learning",
    "LLM", "large language model", "GPT", "ChatGPT", "OpenAI", "Claude",
    "Anthropic", "Gemini", "Gemma", "Llama", "Mistral", "DeepSeek",
    "transformer", "diffusion", "neural network", "agent", "copilot",
    "generative", "multimodal", "RAG", "fine-tun", "alignment",
    "reasoning", "token", "embedding", "vector", "GPU", "H100",
    "H200", "B200", "AI PC", "NPU", "parameter", "open source",
    "frontier model", "safety", "alignment",
]


def _is_ai_related(text: str) -> bool:
    """粗略判断文本是否与 AI 相关。"""
    lower = text.lower()
    return any(kw.lower() in lower for kw in AI_KEYWORDS)


def _parse_feed(source_name: str, feed_label: str, url: str) -> list:
    """抓取并解析单个 RSS/Atom feed，返回标准化事件列表。"""
    events = []
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; WechatAgent/1.0)"
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        logger.warning("RSS 抓取失败 [%s] %s: %s", source_name, url, e)
        return events

    for entry in feed.entries[:20]:  # 每个源最多取 20 条
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = (entry.get("summary") or entry.get("description") or "").strip()
        pub_date = entry.get("published_parsed") or entry.get("updated_parsed")

        if not title or not link:
            continue

        # 过滤非 AI 相关
        combined = f"{title} {summary}"
        if not _is_ai_related(combined):
            continue

        # 时间处理 + 时效过滤
        published_at = ""
        time_reason = "feed timestamp"
        if pub_date:
            try:
                dt = datetime(*pub_date[:6], tzinfo=timezone.utc)
                published_at = dt.isoformat()
                # 跳过超过时间窗口的旧条目
                now = datetime.now(timezone.utc)
                if (now - dt) > timedelta(hours=SECONDARY_WINDOW_HOURS):
                    continue
            except (ValueError, OverflowError):
                pass

        events.append({
            "title": title,
            "summary": summary[:260],
            "source_name": source_name,
            "source_url": link,
            "event_type": "release",
            "published_at": published_at,
            "time_reason": time_reason,
            "freshness": 15,
            "official_score": 15,
            "user_relevance": 14,
            "product_value": 10,
            "account_fit": 12,
            "community_signal_score": 10,
            "user_hook": "",
            "overview": "",
        })

    logger.info("RSS [%s] 抓取到 %d 条事件", source_name, len(events))
    return events


def fetch_all() -> list:
    """抓取所有 RSS 源，返回合并后的标准化事件列表。"""
    all_events = []
    for source_name, label, url in FEEDS:
        events = _parse_feed(source_name, label, url)
        all_events.extend(events)
    logger.info("RSS 总计抓取到 %d 条事件", len(all_events))
    return all_events
