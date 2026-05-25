"""事件选择器模块。

整合评分、过滤、去重、多样性模块，输出最终事件列表和选题报告。
"""

import json
import logging
from datetime import datetime, timezone

from config.settings import MAX_EVENTS, OUTPUT_DIR
from selection.scorer import score_event
from selection.filter import exclude_events
from selection.dedup import deduplicate
from selection.diversifier import diversify

logger = logging.getLogger(__name__)


def select(events: list) -> dict:
    """执行完整选择流程，返回选择结果。"""
    logger.info("开始事件选择: %d 条候选", len(events))

    # Step 1: 评分
    scored = [score_event(e) for e in events]

    # Step 2: 过滤
    filtered, excluded = exclude_events(scored)
    logger.info("过滤后: %d 条保留, %d 条排除", len(filtered), len(excluded))

    # Step 3: 去重
    deduped = deduplicate(filtered)
    logger.info("去重后: %d 条", len(deduped))

    # Step 4: 按总分排序
    deduped.sort(key=lambda e: e.get("total_score", 0), reverse=True)

    # Step 5: 取 top N
    top = deduped[:MAX_EVENTS]

    # Step 6: 多样性控制
    final = diversify(top)

    # 如果多样性控制移除了事件，从排序列表中补充
    if len(final) < len(top):
        remaining = [e for e in deduped[MAX_EVENTS:] if e not in final]
        for e in remaining:
            if len(final) >= MAX_EVENTS:
                break
            final.append(e)
        logger.info("多样性补充后: %d 条", len(final))

    logger.info("最终选择 %d 条事件", len(final))

    result = {
        "selected_events": final,
        "excluded_events": excluded,
        "pool_count": len(events),
        "filtered_count": len(filtered),
        "deduped_count": len(deduped),
        "final_count": len(final),
    }

    return result


def write_selection_report(result: dict) -> str:
    """将选择结果写入选题报告 Markdown 文件。"""
    report = _build_report(result)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "topic-selection-report.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("选题报告已写入: %s", path)
    return str(path)


def _build_report(result: dict) -> str:
    """构建选题报告 Markdown 内容。"""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# 选题报告\n")
    lines.append(f"生成时间: {now}\n")
    lines.append(f"## 统计\n")
    lines.append(f"- 候选池: {result['pool_count']} 条")
    lines.append(f"- 过滤后: {result['filtered_count']} 条")
    lines.append(f"- 去重后: {result['deduped_count']} 条")
    lines.append(f"- 最终入选: {result['final_count']} 条\n")

    lines.append(f"## 入选事件\n")
    for i, e in enumerate(result["selected_events"], 1):
        lines.append(f"### {i}. {e.get('title', '')}")
        lines.append(f"- 来源: {e.get('source_name', '')}")
        lines.append(f"- 总分: {e.get('total_score', 0)}")
        lines.append(f"- 眼球分: {e.get('eye_score', 0)}")
        lines.append(f"- 速览: {e.get('overview', '')}")
        lines.append(f"- 钩子: {e.get('user_hook', '')}")
        lines.append(f"- URL: {e.get('source_url', '')}")
        lines.append("")

    if result["excluded_events"]:
        lines.append(f"## 排除事件\n")
        for title, reason in result["excluded_events"]:
            lines.append(f"- {title}: {reason}")

    return "\n".join(lines)
