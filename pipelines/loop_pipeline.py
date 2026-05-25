"""数据闭环 pipeline。

拉后台数据 → 分析表现 → 更新策略记忆 → 生成分析报告。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


def run_loop():
    """运行数据闭环。"""
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 加载策略记忆
    from memory.strategy_memory import load as load_strategy
    logger.info("Step 1/4: 加载策略记忆")
    strategy = load_strategy()
    logger.info("当前高表现类型: %s", strategy.get("high_perf_types"))
    logger.info("当前低表现类型: %s", strategy.get("low_perf_types"))

    # Step 2: 拉取微信后台数据（需要已发布文章 + access_token）
    from memory.stats_fetcher import save_performance
    logger.info("Step 2/4: 拉取微信后台数据")
    performance = _try_fetch_with_token()

    # 保存原始数据
    if performance:
        save_performance(performance)
        logger.info("表现数据已持久化")
    else:
        logger.info("无表现数据（微信 API 需要 access_token 和已发布文章）")

    # Step 3: 更新策略记忆
    from memory.strategy_memory import update_from_performance
    logger.info("Step 3/4: 更新策略记忆")
    updated = update_from_performance(performance or {})
    logger.info("策略已更新")

    # Step 4: 生成分析报告
    logger.info("Step 4/4: 生成分析报告")
    report = _build_report(strategy, updated, performance)
    report_path = output_dir / "performance-report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("分析报告: %s", report_path)

    return {
        "strategy_before": strategy,
        "strategy_after": updated,
        "performance": performance,
        "report": str(report_path),
    }


def _try_fetch_with_token() -> dict:
    """用微信 API 拉取已发布文章的表现数据。"""
    try:
        from publishing.wechat_api import WeChatClient
        wechat = WeChatClient()
        token = wechat.get_access_token()
        if not token:
            return {}

        from memory.stats_fetcher import fetch_recent_articles, fetch_article_total
        articles = fetch_recent_articles(token, days=7)
        if not articles:
            logger.info("没有找到已发布文章数据")
            return {}

        total = {}
        for article in articles:
            aid = article.get("article_id")
            if aid:
                stats = fetch_article_total(token, aid)
                if stats:
                    total[article.get("title", aid)] = stats
                    for title, s in stats.items():
                        logger.info("  %s: 阅读 %d | 分享 %d | 收藏 %d",
                                    title[:30], s.get("reads", 0), s.get("shares", 0), s.get("collects", 0))

        if not total:
            logger.info("getarticlesummary 返回了文章列表，但 getarticletotal 未获取到详情（可能需要发布超过 24h 才有数据）")

        return total
    except Exception as e:
        logger.warning("微信 API 数据拉取失败: %s", e)
        return {}


def _build_report(old: dict, new: dict, performance: dict) -> str:
    """构建分析报告 Markdown。"""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# 表现分析报告\n")
    lines.append(f"生成时间: {now}\n")

    lines.append("## 策略变化\n")
    lines.append(f"- 高表现类型: {old.get('high_perf_types')} → {new.get('high_perf_types')}")
    lines.append(f"- 低表现类型: {old.get('low_perf_types')} → {new.get('low_perf_types')}")
    lines.append(f"- 标题策略: {old.get('title_strategy')} → {new.get('title_strategy')}")
    lines.append("")

    if performance:
        lines.append("## 近 7 天表现\n")
        lines.append("| 文章 | 阅读数 | 分享数 | 收藏数 | 阅读率 |")
        lines.append("|------|--------|--------|--------|--------|")
        for title, stats in sorted(performance.items(),
                                    key=lambda x: x[1].get("reads", 0), reverse=True):
            lines.append(
                f"| {title[:30]} | {stats.get('reads', 0)} | "
                f"{stats.get('shares', 0)} | {stats.get('collects', 0)} | "
                f"{stats.get('read_rate', 0):.1%} |"
            )
    else:
        lines.append("## 近 7 天表现\n")
        lines.append("*无数据。需要发布文章后才能拉取表现数据。*\n")

    if new.get("event_type_performance"):
        lines.append("## 事件类型表现\n")
        for etype, rate in sorted(new["event_type_performance"].items(),
                                   key=lambda x: x[1], reverse=True):
            lines.append(f"- {etype}: 阅读率 {rate:.1%}")

    return "\n".join(lines)
