"""事件去重模块。

URL 去重 + 标题相似度去重（字符 bigram Jaccard）。
"""

import logging
from typing import Set

from config.settings import DEDUP_SIMILARITY_THRESHOLD
from memory.event_history import get_titles

logger = logging.getLogger(__name__)


def deduplicate(events: list) -> list:
    """对事件列表去重，返回去重后的事件列表。

    去重规则：
    1. URL 标准化去重（内部）
    2. 标题相似度去重（内部）
    3. 对比历史已发事件
    """
    # 1. URL 去重
    seen_urls: Set[str] = set()
    url_deduped = []
    for e in events:
        url = _normalize_url(e.get("source_url", ""))
        if url and url not in seen_urls:
            seen_urls.add(url)
            url_deduped.append(e)
        elif not url:
            url_deduped.append(e)

    # 2. 标题相似度去重
    title_deduped = []
    for e in url_deduped:
        if not _has_duplicate_title(e.get("title", ""), title_deduped):
            title_deduped.append(e)

    # 3. 对比历史
    history_titles = get_titles()
    final = []
    for e in title_deduped:
        if not _has_duplicate_title(e.get("title", ""), history_titles, as_list=True):
            final.append(e)

    logger.info("去重: %d → %d (URL去重) → %d (标题去重) → %d (历史对比)",
                len(events), len(url_deduped), len(title_deduped), len(final))
    return final


def _normalize_url(url: str) -> str:
    """标准化 URL：去掉末尾斜杠、常见 tracking 参数。"""
    if not url:
        return ""
    url = url.strip().rstrip("/")
    import re
    url = re.sub(r"\?utm_.*$", "", url)
    url = re.sub(r"\?ref=.*$", "", url)
    return url.lower()


def _bigram_jaccard(a: str, b: str) -> float:
    """计算两个字符串的字符 bigram Jaccard 相似度。"""
    if not a or not b:
        return 0.0

    def bigrams(s: str) -> Set[str]:
        return {s[i:i+2] for i in range(len(s) - 1)}

    big_a = bigrams(a.lower())
    big_b = bigrams(b.lower())

    if not big_a or not big_b:
        return 0.0

    intersection = big_a & big_b
    union = big_a | big_b
    return len(intersection) / len(union)


def _has_duplicate_title(title: str, existing: list, as_list: bool = False) -> bool:
    """检查标题是否与已有列表中的标题相似。"""
    if as_list:
        known_titles = existing
    else:
        known_titles = [e.get("title", "") for e in existing]

    for known in known_titles:
        if not known:
            continue
        sim = _bigram_jaccard(title, known)
        if sim >= DEDUP_SIMILARITY_THRESHOLD:
            return True
    return False
